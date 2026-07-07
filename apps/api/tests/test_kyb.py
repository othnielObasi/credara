import pytest
from app.modules.kyb.providers.mock_provider import derive_mock_decision


def test_mock_kyb_approves_normal_business():
    status, risk, flags = derive_mock_decision({'legal_name': 'Acme Ltd', 'country': 'GB', 'registration_number': '12345'})
    assert status == 'approved'
    assert risk == 'low'
    assert flags == []


def test_mock_kyb_rejects_block_registration():
    status, risk, flags = derive_mock_decision({'legal_name': 'Bad Ltd', 'country': 'GB', 'registration_number': '123BLOCK'})
    assert status == 'rejected'
    assert risk == 'high'
    assert flags[0]['flag_type'] == 'REGISTRATION_MISMATCH'
