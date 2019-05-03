#
# Tests for the electrolyte submodels
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals
import pybamm
from pybamm.solvers.scikits_ode_solver import scikits_odes_spec
import tests
import numbers
import numpy as np

import unittest


@unittest.skipIf(scikits_odes_spec is None, "scikits.odes not installed")
class TestMacInnesStefanMaxwell(unittest.TestCase):
    def test_basic_processing(self):
        # Parameters
        param = pybamm.standard_parameters_lithium_ion

        # Variables and reactions
        phi_e = pybamm.standard_variables.phi_e
        c_e = pybamm.standard_variables.c_e
        onen = pybamm.Broadcast(1, ["negative electrode"])
        onep = pybamm.Broadcast(1, ["positive electrode"])
        reactions = {
            "main": {"neg": {"s_plus": 1, "aj": onen}, "pos": {"s_plus": 1, "aj": onep}}
        }

        # Set up model
        model = pybamm.electrolyte_current.MacInnesStefanMaxwell(param)
        model.set_algebraic_system(phi_e, c_e, reactions)

        # some small changes so that tests pass
        i_e = model.variables["Electrolyte current density"]
        model.algebraic.update({c_e: c_e - pybamm.Scalar(1)})
        model.initial_conditions.update({c_e: pybamm.Scalar(1)})
        model.boundary_conditions = {
            c_e: {"left": 1},
            phi_e: {"left": 0},
            i_e: {"right": 0},
        }

        # Test
        modeltest = tests.StandardModelTest(model)
        modeltest.test_all()

    def test_explicit(self):
        param = pybamm.standard_parameters_lithium_ion

        # Set up
        c_e_n = pybamm.Broadcast(1, domain=["negative electrode"])
        c_e_s = pybamm.Broadcast(1, domain=["separator"])
        c_e_p = pybamm.Broadcast(1, domain=["positive electrode"])
        c_e = pybamm.Concatenation(c_e_n, c_e_s, c_e_p)

        ocp_n = pybamm.Scalar(0)
        eta_r_n = pybamm.Scalar(0)
        phi_s_n = pybamm.Scalar(0)

        # electrode model
        # electrode_model = pybamm.electrode.Ohm(param)
        # phi_s_n = electrode_model.get_neg_pot_explicit_combined()

        # Model
        model = pybamm.electrolyte_current.MacInnesStefanMaxwell(param)
        leading_order_vars = model.get_explicit_leading_order(ocp_n, eta_r_n)
        combined_vars = model.get_explicit_combined(ocp_n, eta_r_n, c_e, phi_s_n)

        # Get disc
        modeltest = tests.StandardModelTest(model)

        for order, out_vars in [
            ("leading", leading_order_vars),
            ("combined", combined_vars),
        ]:
            # Process parameters
            for name, var in out_vars.items():
                out_vars[name] = modeltest.parameter_values.process_symbol(var)

            # Unpack
            phi_e = out_vars["Electrolyte potential"]
            i_e = out_vars["Electrolyte current density"]
            delta_phi_e_av = out_vars["Average electrolyte ohmic losses"]
            eta_c_av = out_vars["Average concentration overpotential"]

            # Test
            self.assertIsInstance(phi_e, pybamm.Concatenation)
            self.assertIsInstance(i_e, pybamm.Concatenation)
            self.assertIsInstance(delta_phi_e_av, pybamm.Symbol)
            self.assertIsInstance(eta_c_av, pybamm.Symbol)

            phi_e_disc = modeltest.disc.process_symbol(phi_e)
            phi_e_eval = phi_e_disc.evaluate(0, None)

            i_e_disc = modeltest.disc.process_symbol(i_e)
            i_e_eval = i_e_disc.evaluate(0, None)

            delta_phi_e_disc = modeltest.disc.process_symbol(delta_phi_e_av)
            delta_phi_e_eval = delta_phi_e_disc.evaluate(0, None)

            self.assertTrue(type(phi_e_eval) is np.ndarray)
            self.assertTrue(type(i_e_eval) is np.ndarray)
            self.assertIsInstance(delta_phi_e_eval, numbers.Number)

            np.testing.assert_array_less(0, i_e_eval)
            np.testing.assert_array_less(i_e_eval, 1.01)

            if order == "leading":
                self.assertEqual(delta_phi_e_eval, 0)
            elif order == "combined":
                self.assertLess(delta_phi_e_eval, 0)

            # check that left boundary of phi_e is approx 0
            phi_e_left = pybamm.BoundaryValue(phi_e, "left")
            phi_e_left_disc = modeltest.disc.process_symbol(phi_e_left)
            phi_e_left_eval = phi_e_left_disc.evaluate(0, None)

            if order == "leading":
                np.testing.assert_almost_equal(
                    phi_e_left_eval, 0, 3
                )  # extrapolation error
            elif order == "combined":
                i_cell = param.current_with_time
                eps_n, _, _ = [e.orphans[0] for e in param.epsilon.orphans]
                kappa_n = param.kappa_e(1) * eps_n ** param.b
                true_val = param.C_e * i_cell * param.l_n / 6 / param.gamma_e / kappa_n

                true_val_param = modeltest.parameter_values.process_symbol(true_val)
                true_val_disc = modeltest.disc.process_symbol(true_val_param)
                true_val_eval = true_val_disc.evaluate(0, None)

                np.testing.assert_almost_equal(
                    phi_e_left_eval, true_val_eval, 3
                )  # extrapolation error


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
