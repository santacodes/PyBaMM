#
# Single Particle Model (SPM)
#
import pybamm


class SPM(pybamm.LithiumIonBaseModel):
    """Single Particle Model (SPM) of a lithium-ion battery.
    **Extends:** :class:`pybamm.LithiumIonBaseModel`
    """

    def __init__(self, options=None):
        super().__init__()
        self.name = "Single Particle Model"

        "-----------------------------------------------------------------------------"
        "Parameters"
        param = self.set_of_parameters

        "-----------------------------------------------------------------------------"
        "Model Variables"
        c_s_n = pybamm.standard_variables.c_s_n
        c_s_p = pybamm.standard_variables.c_s_p

        "-----------------------------------------------------------------------------"
        "Boundary conditions"
        v_boundary_cc = pybamm.Variable("Current collector voltage", domain="current collector")
        i_boundary_cc = pybamm.Variable("Current collector current density", domain="current collector")
        bc_variables = {"i_boundary_cc": i_boundary_cc, "v_boundary_cc": v_boundary_cc}
        self.set_boundary_conditions(bc_variables)

        "-----------------------------------------------------------------------------"
        "Submodels"

        # Interfacial current density
        neg = ["negative electrode"]
        pos = ["positive electrode"]
        int_curr_model = pybamm.interface.LithiumIonReaction(param)
        j_n = int_curr_model.get_homogeneous_interfacial_current(i_boundary_cc, neg)
        j_p = int_curr_model.get_homogeneous_interfacial_current(i_boundary_cc, pos)

        # Particle models
        negative_particle_model = pybamm.particle.Standard(param)
        negative_particle_model.set_differential_system(c_s_n, j_n, broadcast=True)
        positive_particle_model = pybamm.particle.Standard(param)
        positive_particle_model.set_differential_system(c_s_p, j_p, broadcast=True)
        self.update(negative_particle_model, positive_particle_model)

        "-----------------------------------------------------------------------------"
        "Post-Processing"

        # Electrolyte concentration
        c_e = pybamm.Scalar(1)
        N_e = pybamm.Scalar(0)
        electrolyte_conc_model = pybamm.electrolyte_diffusion.StefanMaxwell(param)
        conc_vars = electrolyte_conc_model.get_variables(c_e, N_e)
        self.variables.update(conc_vars)

        # Exchange-current density
        c_s_n_surf = pybamm.surf(c_s_n)
        c_s_p_surf = pybamm.surf(c_s_p)
        j0_n = int_curr_model.get_exchange_current_densities(c_e, c_s_n_surf, neg)
        j0_p = int_curr_model.get_exchange_current_densities(c_e, c_s_p_surf, pos)
        j_vars = int_curr_model.get_derived_interfacial_currents(j_n, j_p, j0_n, j0_p)
        self.variables.update(j_vars)

        # Potentials
        ocp_n = param.U_n(c_s_n_surf)
        ocp_p = param.U_p(c_s_p_surf)
        eta_r_n = int_curr_model.get_inverse_butler_volmer(j_n, j0_n, neg)
        eta_r_p = int_curr_model.get_inverse_butler_volmer(j_p, j0_p, pos)
        pot_model = pybamm.potential.Potential(param)
        ocp_vars = pot_model.get_derived_open_circuit_potentials(ocp_n, ocp_p)
        eta_r_vars = pot_model.get_derived_reaction_overpotentials(eta_r_n, eta_r_p)
        self.variables.update({**ocp_vars, **eta_r_vars})

        # Electrolyte current
        eleclyte_current_model = pybamm.electrolyte_current.MacInnesStefanMaxwell(param)
        elyte_vars = eleclyte_current_model.get_explicit_leading_order(self.variables)
        self.variables.update(elyte_vars)

        # Electrode
        electrode_model = pybamm.electrode.Ohm(param)
        electrode_vars = electrode_model.get_explicit_leading_order(self.variables)
        self.variables.update(electrode_vars)

        # Cut-off voltage
        voltage = self.variables["Terminal voltage"]
        self.events.append(voltage - param.voltage_low_cut)

    @property
    def default_geometry(self):
        dimensionality = self.options["bc_options"]["dimensionality"]
        if dimensionality == 0:
            return pybamm.Geometry("1D macro", "1D micro")
        elif dimensionality == 1:
            return pybamm.Geometry("1+1D macro", "1D micro")
        elif dimensionality == 2:
            return pybamm.Geometry("2+1D macro", "1D micro")

    @property
    def default_submesh_types(self):
        dimensionality = self.options["bc_options"]["dimensionality"]
        if dimensionality in [0, 1]:
            return {
                "negative electrode": pybamm.Uniform1DSubMesh,
                "separator": pybamm.Uniform1DSubMesh,
                "positive electrode": pybamm.Uniform1DSubMesh,
                "negative particle": pybamm.Uniform1DSubMesh,
                "positive particle": pybamm.Uniform1DSubMesh,
                "current collector": pybamm.Uniform1DSubMesh,
            }
        elif dimensionality == 2:
            return {
                "negative electrode": pybamm.Uniform1DSubMesh,
                "separator": pybamm.Uniform1DSubMesh,
                "positive electrode": pybamm.Uniform1DSubMesh,
                "negative particle": pybamm.Uniform1DSubMesh,
                "positive particle": pybamm.Uniform1DSubMesh,
                "current collector": pybamm.FenicsMesh2D,
            }

    @property
    def default_spatial_methods(self):
        dimensionality = self.options["bc_options"]["dimensionality"]
        if dimensionality in [0, 1]:
            return {
                "macroscale": pybamm.FiniteVolume,
                "negative particle": pybamm.FiniteVolume,
                "positive particle": pybamm.FiniteVolume,
                "current collector": pybamm.FiniteVolume,
            }
        elif dimensionality == 2:
            return {
                "macroscale": pybamm.FiniteVolume,
                "negative particle": pybamm.FiniteVolume,
                "positive particle": pybamm.FiniteVolume,
                "current collector": pybamm.FiniteElementFenics,
            }

    def set_boundary_conditions(self, bc_variables=None):
        """Get boundary conditions"""
        # TODO: edit to allow constant-current and constant-power control
        param = self.set_of_parameters
        dimensionality = self.options["bc_options"]["dimensionality"]
        if dimensionality == 0:
            current_bc = param.current_with_time
            self.variables["Current collector current density"] = current_bc
            # TO DO: fix voltage here
            voltage = pybamm.Scalar(1)
            self.variables["Current collector voltage"] = voltage
        elif dimensionality == 1:
            raise NotImplementedError
        elif dimensionality == 2:
            i_boundary_cc = bc_variables["i_boundary_cc"]
            v_boundary_cc = bc_variables["v_boundary_cc"]
            current_collector_model = pybamm.current_collector.OhmTwoDimensional(param)
            current_collector_model.set_algebraic_system(v_boundary_cc, i_boundary_cc)
            self.update(current_collector_model)
