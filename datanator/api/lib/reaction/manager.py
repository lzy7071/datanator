"""
:Author: Yosef Roth <yosefdroth@gmail.com>
:Author: Jonathan Karr <jonrkarr@gmail.com>
:Author: Saahith Pochiraju <saahith116@gmail.com>
:Date: 2017-05-16
:Copyright: 2017, Karr Lab
:License: MIT
"""

from datanator.core import data_model, data_query, models, common_schema
from datanator.util import molecule_util
from wc_utils.util import string
import sqlalchemy
from datanator.api.lib.data_manager import BaseManager
from datanator.util.constants import DATA_CACHE_DIR

class ReactionManager(BaseManager):
    """ Finds relevant kinetics observations for reactions

    1. Find kinetics observed for the reaction or similar reactions

      a. Find kinetics observed for the reaction

        i. Find the metabolite(s) of each participant
        ii. Find the  reaction(s) which contain all of these metabolites
        iii. Find the  kinetic laws associated with these reactions

      b. Find kinetics observed for similar reactions

        i. Find kinetics observed for the assigned EC number(s)
        ii. Find kinetics observed for EC number(s) predicted by tools such as E-zyme

    2. Filter out observations from disimilar genetic and environmental conditions and
       rank the remaing observations by their similarity to the desired genetic and environmental
       conditions
    3. Calculate a statistical representation of the relevant observations
    """

    def __init__(self, cache_dirname = DATA_CACHE_DIR):
        self.data_source = common_schema.CommonSchema(cache_dirname=cache_dirname)

    def get_observed_parameter_value(self, reaction):
        """ Find observed kinetics for the reaction or similar reactions
        TODO: Add compartment infomrmation

        1. Find kinetics observed for the reaction

          a. Find the metabolite(s) of each participant
          b. Find the reaction(s) which contain all of these metabolites
          c. Find the kinetic laws associated with these reactions

        2. Find kinetics observed for similar reactions

          a. Find kinetics observed for the assigned EC number(s)
          b. Find kinetics observed for EC number(s) predicted by tools such as E-zyme

        Args:
            reaction (:obj:`data_model.Reaction`): reaction to find data for

        Returns:
            :obj:`list` of :obj:`data_model.ObservedValue`: list of relevant observed values
        """

        q_law = self.get_kinetic_laws_by_reaction(reaction)
        observed_vals = []
        for law in q_law:
            common_schema_reaction_id = next(xr._id for xr in law._metadata.resource if xr.namespace == 'sabiork.reaction')

            reaction = data_model.Reaction(
                cross_references=[
                    data_model.Resource(namespace='common_schema.kinetic_law_id', id=str(law.kinetic_law_id)),
                    data_model.Resource(namespace='sabiork.reaction', id=common_schema_reaction_id),
                ],
            )
            species = {}
            compartments = {}

            cs_rxn = self.data_source.session.query(models.Reaction).filter_by(kinetic_law_id = law.kinetic_law_id)
            reactants = cs_rxn.filter_by(_is_reactant = True).all()
            products = cs_rxn.filter_by(_is_product = True).all()
            modifiers = cs_rxn.filter_by(_is_modifier = True).all()


            for reactant in reactants:
                part = data_model.ReactionParticipant(coefficient=-1)

                if reactant.metabolite_id not in species:
                    species[reactant.metabolite_id] = data_model.Specie(name=reactant.metabolite.metabolite_name)
                part.specie = species[reactant.metabolite_id]

                if reactant.metabolite.structure_id:
                    part.specie.structure = reactant.metabolite.structure._value_inchi

                if reactant.compartment_id:
                    if reactant.compartment.name not in compartments:
                        compartments[reactant.compartment.name] = data_model.Compartment(name=reactant.compartment.name)
                    part.compartment = compartments[reactant.compartment.name]

                reaction.participants.append(part)

            for product in products:
                part = data_model.ReactionParticipant(coefficient=1)

                if product.metabolite_id not in species:
                    species[product.metabolite_id] = data_model.Specie(name=product.metabolite.metabolite_name)
                part.specie = species[product.metabolite_id]

                if product.metabolite.structure_id:
                    part.specie.structure = product.metabolite.structure._value_inchi

                if product.compartment_id:
                    if product.compartment.name not in compartments:
                        compartments[product.compartment.name] = data_model.Compartment(name=product.compartment.name)
                    part.compartment = compartments[product.compartment.name]

                reaction.participants.append(part)

            for modifier in modifiers:
                part = data_model.ReactionParticipant(coefficient=0)

                if modifier.metabolite_id not in species:
                    species[modifier.metabolite_id] = data_model.Specie(name=modifier.metabolite.metabolite_name)
                part.specie = species[modifier.metabolite_id]

                if modifier.metabolite.structure_id:
                    part.specie.structure = modifier.metabolite.structure._value_inchi

                if modifier.compartment_id:
                    if modifier.compartment.name not in compartments:
                        compartments[modifier.compartment.name] = data_model.Compartment(name=modifier.compartment.name)
                    part.compartment = compartments[modifier.compartment.name]

                reaction.participants.append(part)

            metadata = self.metadata_dump(law)

            for parameter in law.parameter:
                if parameter.value is None:
                    continue

                observable = data_model.Observable(
                    interaction=reaction,
                    property=parameter.observed_name,
                )

                if parameter.metabolite_id:
                    observable.specie = species[parameter.metabolite_id]
                    # if parameter.compartment:
                    #     observable.compartment = data_model.Compartment(
                    #         id=parameter.compartment.name,
                    #     )

                observed_vals.append(data_model.ObservedValue(
                    metadata=metadata,
                    observable=observable,
                    value=parameter.value,
                    error=parameter.error,
                    units=parameter.units,
                ))

        return observed_vals


    def _port(self, reaction_list):
        """
        Converts SQL model reaction into a Obj Model based data_model reaction

        Args:
            reaction_list :obj:`list` of :obj:`models.Reaction`:): list of reaction participants

        Returns:
            :obj:`data_model.Reaction`: a cohesive reaction data object


        """

        references = []
        participants = []
        for rxn_part in reaction_list:
            if rxn_part._is_reactant:
                coef = -1
            elif rxn_part._is_product:
                coef = 1
            elif rxn_part._is_modifier:
                coef = 0

            part = data_model.ReactionParticipant(
                specie = data_model.Specie(
                    name = rxn_part.metabolite.metabolite_name,
                    structure = rxn_part.metabolite.structure._value_inchi if rxn_part.metabolite.structure else None ),
                coefficient = coef)
            participants.append(part)

            if len(references)<1:
                for item in rxn_part.kinetic_law._metadata.resource:
                    references.append(data_model.Resource(namespace=item.namespace, id=item._id, assignment_method=data_model.ResourceAssignmentMethod.manual))

        rxn = data_model.Reaction(participants = participants, cross_references=references, kinetic_law_id=reaction_list[0].kinetic_law_id)
        rxn.name = rxn.stringify()

        return rxn


    def get_reaction_by_kinetic_law_id(self, id):
        rxn_list = self.data_source.session.query(models.Reaction).filter_by(kinetic_law_id=id).all()
        return self._port(rxn_list)


    def get_reaction_by_metabolite(self, metabolite, select=models.Reaction):
        """ Get reaction that contains the metabolite role :obj:`models.Metabolite`

        Args:
            structure (:obj:`models.Metabolite`): InChI structure or formula and connectivity layers to search for

        Returns:
            :obj:`data_model.Reaction`: reaction to find data for
        """

        rxn_cluster= [self.data_source.session.query(models.Reaction).filter_by(kinetic_law_id=rxn.kinetic_law_id).all() for rxn in metabolite.reaction]

        reaction_list = []
        for rxn in rxn_cluster:
            reaction= self._port(rxn)
            reaction_list.append(reaction)


        return reaction_list


    def get_kinetic_laws_by_reaction(self, reaction, select=models.KineticLaw):
        """ Get kinetic laws that were observed for similar reactions (same participants or same EC class)

        Args:
            reaction (:obj:`data_model.Reaction`): reaction to find data for

        Returns:
            :obj:`list` of :obj:`models.KineticLaw`: a list kinetic laws that contain all of the participants
        """

        # by participants
        participants = reaction.participants
        q = self.get_kinetic_laws_by_participants(participants, select=select)
        if len(q):
            return q

        # by assigned EC numbers
        ec_numbers = [xr.id for xr in reaction.get_manual_ec_numbers()]
        q = self.get_kinetic_laws_by_ec_numbers(ec_numbers, select=select)
        if q.count():
            return q.all()

        # by predicted EC numbers
        ec_numbers = [xr.id for xr in reaction.get_predicted_ec_numbers()]
        q = self.get_kinetic_laws_by_ec_numbers(ec_numbers, select=select)
        if q.count():
            return q.all()

        # return empty list if no relevant observations were found
        return self.data_source.session.query(select).filter_by(id=-1)


    def get_kinetic_laws_by_participants(self, participants, only_formula_and_connectivity=False, include_water_hydrogen=False,
                                         select=models.KineticLaw):
        """ Get kinetic laws with the participants :obj:`participants`

        Args:
            participants (:obj:`list` of :obj:`data_model.ReactionParticipant`): list of reaction participants
            only_formula_and_connectivity (:obj:`bool`, optional): if :obj:`True`, find kinetic laws which contain species with the same
                InChI formula and connectivity layers
            include_water_hydrogen (:obj:`bool`, optional): if :obj:`True`, restrict kinetic laws based on their water, hydroxide, and
                hydrogen participants

        Returns:
            :obj:`list` of :obj:`models.KineticLaw`: a list kinetic laws that contain all of the participants

        """
        q_laws = None
        for i_part, part in enumerate(participants):
            if only_formula_and_connectivity == True:
                try:
                    structure = part.specie.to_inchi(only_formula_and_connectivity=only_formula_and_connectivity)
                except ValueError:
                    return self.data_source.session.query(select).filter(common_schema.KineticLaw.kinetic_law_id == -1)
            else:
                structure = part.specie.structure

            if not include_water_hydrogen:
                if only_formula_and_connectivity:
                    formula_and_connectivity = structure
                else:
                    if structure:
                        formula_and_connectivity = part.specie.to_inchi(only_formula_and_connectivity=True)
                # if formula_and_connectivity in ['', 'H2O', 'H2O']:
                #     continue

            role = None
            if part.coefficient < 0:
                role = 'reactant'
            elif part.coefficient > 0:
                role = 'product'

            q_part = self.get_kinetic_laws_by_structure(structure, role=role)

            if not q_laws:
                q_laws = q_part
            else:
                q_laws = [val for val in q_laws if val in q_part]

        return q_laws

    def get_kinetic_laws_by_structure(self, structure, only_formula_and_connectivity=False, role='reactant', select=models.KineticLaw):
        """ Get kinetic laws that contain a structure in role :obj:`role`

        Args:
            structure (:obj:`str`): InChI structure or formula and connectivity layers to search for
            only_formula_and_connectivity (:obj:`bool`, optional): if :obj:`True`, find kinetic laws which contain species with the same
                InChI formula and connectivity layers
            role (:obj:`str`, optional): role (reactant, or product) to search for species

        Returns:
            :obj:`sqlalchemy.orm.query.Query`: query for kinetic laws that contain the structure in role :obj:`role`
        """

        if only_formula_and_connectivity:
            condition = models.Structure._structure_formula_connectivity == structure
        else:
            condition = models.Structure._value_inchi == structure

        if role == 'reactant':
            participant_condition = models.Reaction._is_reactant == True
        elif role == 'product':
            participant_condition = models.Reaction._is_product == True
        else:
            participant_condition = models.Reaction._is_modifier == True

        session = self.data_source.session

        law = session.query(select).join(models.Reaction, models.KineticLaw.kinetic_law_id == models.Reaction.kinetic_law_id)\
            .filter(participant_condition).join(models.Metabolite, models.Reaction.metabolite)\
            .join(models.Structure, models.Metabolite.structure).filter(condition)

        return law

    def get_kinetic_laws_by_metabolite(self, metabolite, role='reactant', select=models.KineticLaw):
        """ Get kinetic laws that contain a structure in role :obj:`role`

        Args:
            structure (:obj:`str`): InChI structure or formula and connectivity layers to search for
            only_formula_and_connectivity (:obj:`bool`, optional): if :obj:`True`, find kinetic laws which contain species with the same
                InChI formula and connectivity layers
            role (:obj:`str`, optional): role (reactant, or product) to search for species

        Returns:
            :obj:`sqlalchemy.orm.query.Query`: query for kinetic laws that contain the structure in role :obj:`role`
        """


        condition = models.Metabolite.metabolite_id == metabolite.metabolite_id

        if role == 'reactant':
            participant_condition = models.Reaction._is_reactant == True
        elif role == 'product':
            participant_condition = models.Reaction._is_product == True
        elif role == 'modifier':
            participant_condition = models.Reaction._is_modifier == True
        else:
            raise ValueError('role does not exist')

        session = self.data_source.session

        law = session.query(select).join(models.Reaction, models.KineticLaw.reaction)\
            .filter(participant_condition).join(models.Metabolite, models.Reaction.metabolite).filter(condition)

        return law

    def get_kinetic_laws_by_ec_numbers(self, ec_numbers, match_levels=4, select=models.KineticLaw):
        """ Get kinetic laws which have one of a list of EC numbers or, optionally,
        belong to one of a list of EC classes.

        Args:
            ec_numbers (:obj:`list` of :obj:`str`): EC numbers to search for
            match_levels (:obj:`int`): number of EC levels that the EC number must match

        Returns:
            :obj:`sqlalchemy.orm.query.Query`: query for matching kinetic laws
        """
        # find kinetic laws with identical EC number
        q = self.data_source.session.query(select) \
            .join((models.Metadata, models.KineticLaw._metadata)).join((models.Resource, models.Metadata.resource))\
            .filter(models.Resource.namespace == 'ec-code')

        if match_levels == 4:
            result = q.filter(models.Resource._id.in_(ec_numbers))
        else:
            conditions = []
            for ec_number in ec_numbers:
                ec_class, _, _ = string.partition_nth(ec_number, '.', match_levels)
                conditions.append(models.Resource._id.like('{}.%'.format(ec_class)))
            result = q.filter(sqlalchemy.or_(*conditions))

        return result

reaction_manager = ReactionManager()
