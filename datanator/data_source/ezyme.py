""" Ezyme

:Author: Yosef Roth <yosefdroth@gmail.com>
:Author: Jonathan <jonrkarr@gmail.com>
:Date: 2017-05-04
:Copyright: 2017, Karr Lab
:License: MIT
"""

from datanator.core import data_model
from datanator.core import data_source
import itertools
import re
import requests


class Ezyme(data_source.WebserviceDataSource):
    """ Utilities for using Ezyme to predict EC numbers.

    See Ezyme (http://www.genome.jp/tools-bin/predict_reaction) for more information.

    Attributes:
        REQUEST_URL (:obj:`str`): URL to request Ezyme EC number prediction
        RETRIEVAL_URL (:obj:`str`): URL to retrieve Ezyme results
        EC_PREDICTION_URL (:obj:`str`): URL where predicted EC number is encoded
    """
    ENDPOINT_DOMAINS = {'ezyme': 'http://www.genome.jp'}
    REQUEST_URL = ENDPOINT_DOMAINS['ezyme'] + '/tools-bin/predict_view'
    RETRIEVAL_URL = ENDPOINT_DOMAINS['ezyme'] + '/tools-bin/e-zyme2/result.cgi'
    EC_PREDICTION_URL = ENDPOINT_DOMAINS['ezyme'] + '/kegg-bin/get_htext?htext=ko01000.keg&query='

    def run(self, reaction):
        """ Use Ezyme to predict the first three digits of the EC number of a reaction.

        Args:
            :obj:`data_model.Reaction`: reaction

        Returns:
            :obj:`list` of :obj:`EzymeResult` or :obj:`None`: ranked list of predicted EC numbers and their scores
                or :obj:`None` if one or more participant doesn't have a defined structure
        """
        if next((part for part in reaction.participants if not part.specie.structure), None):
            return None

        pairs = reaction.get_reactant_product_pairs()

        reactants = []
        products = []
        for pair in pairs:
            if pair[0]:
                reactants.append(pair[0].specie.to_mol())
            if pair[1]:
                products.append(pair[1].specie.to_mol())

        return self._run(reactants, products)

    def _run(self, reactants, products):
        """ Low level interface to use Ezyme to predict the first three digits of the EC number of a reaction.

        Note: The order of the compounds must be the same in the reactants and products list. If you have not manually
        ordered the reactants and products, we recommend that you use the :obj:`run` method which will
        order the reactants and products lists according to their chemical similarity.

        Args:
            reactants (:obj:`list` of :obj:`str`): list of structures of reactants in MOL format
            products (:obj:`list` of :obj:`str`): list of structures of products in MOL format

        Returns:
            :obj:`list` of :obj:`EzymeResult` or :obj:`None`: ranked list of predicted EC numbers and their scores
                or :obj:`None` if one or more participant doesn't have a defined structure
        """
        # return `None` if one or more participant doesn't have a defined structure
        if not all(reactants) or not all(products):
            return None

        # Request Ezyme to predict the EC number
        response = self.requests_session.post(self.REQUEST_URL, data={
            'QUERY_MODE': 'MULTI',
            'S_MOLTEXT': reactants,
            'P_MOLTEXT': products,
        })
        response.raise_for_status()
        file = re.findall('<input type=hidden name=file value="(.*?)">', response.text)[0]

        # retrieve the predicted EC number(s)
        response = self.requests_session.post(self.RETRIEVAL_URL, data={
            'file': file,
            'name': ''.join(':' + str(i) for i, c in enumerate(itertools.chain(reactants, products)))
        })
        response.raise_for_status()
        results = re.findall(
            '<td align=center><a href="{}{}">[0-9]+\.[0-9]+\.[0-9]+</a></td>\n<td align=center>([0-9\.]+)</td>'.format(
                re.escape(self.EC_PREDICTION_URL), '([0-9]+\.[0-9]+\.[0-9]+)\.'),
            response.text, re.MULTILINE)
        return [EzymeResult(r[0], float(r[1])) for r in results]


class EzymeResult(object):
    """ Represents a predicted EC number

    Attributes:
        ec_number (:obj:`str`): EC number
        score (:obj:`float`): score
    """

    def __init__(self, ec_number, score):
        """
        Args:
            ec_number (:obj:`str`): EC number
            score (:obj:`float`): score
        """
        self.ec_number = ec_number
        self.score = score
