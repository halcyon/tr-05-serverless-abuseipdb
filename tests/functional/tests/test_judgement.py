from ctrlibrary.core.utils import get_observables
from ctrlibrary.threatresponse.enrich import enrich_observe_observables
from tests.functional.tests.constants import (
    CTR_ENTITIES_LIMIT,
    MODULE_NAME,
    SOURCE
)


def test_positive_judgement_ip_observable(module_headers):
    """Perform testing for enrich observe observables endpoint to get
    judgement for observable from Abuse IPDB module

    ID: CCTRI-811-4917ba85-fa06-4f9f-b213-2f3a40861766

    Steps:
        1. Send request to enrich observe observable endpoint

    Expectedresults:
        1. Check that data in response body contains expected verdict for
            observable from Abuse IPDB module

    Importance: Critical
    """
    observables = [{'type': 'ip', 'value': '192.168.1.1'}]
    response_from_all_modules = enrich_observe_observables(
        payload=observables,
        **{'headers': module_headers}
    )
    response_from_abuse = get_observables(response_from_all_modules,
                                          MODULE_NAME)

    assert response_from_abuse['module'] == MODULE_NAME
    assert response_from_abuse['module_instance_id']
    assert response_from_abuse['module_type_id']

    judgements = response_from_abuse['data']['judgements']
    assert len(judgements['docs']) > 0
    for judgement in judgements['docs']:
        assert judgement['type'] == 'judgement'
        assert judgement['id'].startswith('transient:judgement-')
        assert judgement['reason']
        assert judgement['disposition'] == 2
        assert judgement['disposition_name'] == 'Malicious'
        assert judgement['source'] == SOURCE
        assert judgement['severity'] == 'Medium'
        assert judgement['confidence'] == 'Medium'
        assert judgement['priority'] == 85

    assert judgements['count'] == len(judgements['docs']) <= CTR_ENTITIES_LIMIT
