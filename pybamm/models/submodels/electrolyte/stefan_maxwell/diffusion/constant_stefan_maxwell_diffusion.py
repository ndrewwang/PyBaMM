#
# Class for leading-order electrolyte diffusion employing stefan-maxwell
#
import pybamm

from .base_stefan_maxwell_diffusion import BaseModel


class ConstantConcentration(BaseModel):
    """Class for conservation of mass in the electrolyte employing the
    Stefan-Maxwell constitutive equations. (Leading refers to leading order
    of asymptotic reduction)

    Parameters
    ----------
    param : parameter class
        The parameters to use for this submodel

    *Extends:* :class:`pybamm.electrolyte.stefan_maxwell.diffusion.BaseModel`
    """

    def __init__(self, param):
        super().__init__(param)

    def get_fundamental_variables(self):
        """
        Returns the variables in the submodel which can be stated independent of
        variables stated in other submodels
        """
        c_e_av = pybamm.Scalar(1)
        c_e_n = pybamm.Broadcast(c_e_av, ["negative electrode"])
        c_e_s = pybamm.Broadcast(c_e_av, ["separator"])
        c_e_p = pybamm.Broadcast(c_e_av, ["positive electrode"])
        c_e = pybamm.Concatenation(c_e_n, c_e_s, c_e_p)

        variables = self._get_standard_concentration_variables(c_e, c_e_av)

        N_e = pybamm.Broadcast(
            0, ["negative electrode", "separator", "positive electrode"]
        )

        variables.update(self._get_standard_flux_variables(N_e))

        return variables

    def set_boundary_conditions(self, variables):
        return {}

