"""Unit tests for appointment models."""

from datetime import date

import pytest

from ukcompanies.models.appointment import (
    Appointment,
    AppointmentList,
    CompanyStatus,
)
from ukcompanies.models.officer import OfficerRole


class TestAppointment:
    """Test Appointment model."""

    @pytest.fixture
    def basic_appointment_data(self):
        """Basic appointment data for tests."""
        return {
            "appointed_to": {
                "company_name": "Test Company Ltd",
                "company_number": "12345678",
                "company_status": "active",
            },
            "name": "John Smith",
            "officer_role": "director",
            "appointed_on": "2020-01-01",
        }

    def test_create_basic_appointment(self, basic_appointment_data):
        """Test creating a basic appointment."""
        appointment = Appointment(**basic_appointment_data)
        assert appointment.name == "John Smith"
        assert appointment.officer_role == OfficerRole.DIRECTOR
        assert appointment.appointed_on == date(2020, 1, 1)

    def test_company_properties(self, basic_appointment_data):
        """Test company property accessors."""
        appointment = Appointment(**basic_appointment_data)
        assert appointment.company_name == "Test Company Ltd"
        assert appointment.company_number == "12345678"
        assert appointment.company_status == "active"

    def test_is_active_not_resigned(self, basic_appointment_data):
        """Test is_active property when not resigned."""
        appointment = Appointment(**basic_appointment_data)
        assert appointment.is_active is True

    def test_is_active_resigned(self, basic_appointment_data):
        """Test is_active property when resigned."""
        basic_appointment_data["resigned_on"] = "2021-12-31"
        appointment = Appointment(**basic_appointment_data)
        assert appointment.is_active is False

    def test_is_corporate_regular(self, basic_appointment_data):
        """Test is_corporate property for regular appointment."""
        appointment = Appointment(**basic_appointment_data)
        assert appointment.is_corporate is False

    def test_is_corporate_true(self, basic_appointment_data):
        """Test is_corporate property for corporate appointment."""
        basic_appointment_data["officer_role"] = "corporate-secretary"
        appointment = Appointment(**basic_appointment_data)
        assert appointment.is_corporate is True

    def test_appointment_with_address(self, basic_appointment_data):
        """Test appointment with address."""
        basic_appointment_data["address"] = {
            "address_line_1": "123 Main St",
            "locality": "London",
            "postal_code": "SW1A 1AA",
        }
        appointment = Appointment(**basic_appointment_data)
        assert appointment.address.address_line_1 == "123 Main St"

    def test_pre_1992_appointment(self, basic_appointment_data):
        """Test pre-1992 appointment flag."""
        basic_appointment_data["is_pre_1992_appointment"] = True
        basic_appointment_data["appointed_before"] = "1992-01-01"
        appointment = Appointment(**basic_appointment_data)
        assert appointment.is_pre_1992_appointment is True
        assert appointment.appointed_before == date(1992, 1, 1)

    def test_appointment_with_identification(self, basic_appointment_data):
        """Test appointment with corporate identification."""
        basic_appointment_data["identification"] = {
            "identification_type": "uk-limited-company",
            "registration_number": "87654321",
        }
        appointment = Appointment(**basic_appointment_data)
        assert appointment.identification["registration_number"] == "87654321"

    def test_appointment_with_all_fields(self, basic_appointment_data):
        """Test appointment with all optional fields."""
        basic_appointment_data.update({
            "nationality": "British",
            "country_of_residence": "United Kingdom",
            "occupation": "Company Director",
            "resigned_on": "2021-06-30",
            "person_number": "123456789",
            "links": {
                "self": "/appointments/abc123",
                "company": "/company/12345678",
            },
        })
        appointment = Appointment(**basic_appointment_data)
        assert appointment.nationality == "British"
        assert appointment.country_of_residence == "United Kingdom"
        assert appointment.occupation == "Company Director"
        assert appointment.person_number == "123456789"


class TestAppointmentList:
    """Test AppointmentList model."""

    @pytest.fixture
    def appointment_list_data(self):
        """Appointment list data for tests."""
        return {
            "items": [
                {
                    "appointed_to": {
                        "company_name": "Company A",
                        "company_number": "11111111",
                        "company_status": "active",
                    },
                    "name": "John Smith",
                    "officer_role": "director",
                    "appointed_on": "2020-01-01",
                },
                {
                    "appointed_to": {
                        "company_name": "Company B",
                        "company_number": "22222222",
                        "company_status": "dissolved",
                    },
                    "name": "John Smith",
                    "officer_role": "secretary",
                    "appointed_on": "2019-01-01",
                    "resigned_on": "2021-01-01",
                },
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 2,
            "name": "John Smith",
            "is_corporate_officer": False,
        }

    def test_create_appointment_list(self, appointment_list_data):
        """Test creating an appointment list."""
        appointment_list = AppointmentList(**appointment_list_data)
        assert len(appointment_list.items) == 2
        assert appointment_list.name == "John Smith"
        assert appointment_list.is_corporate_officer is False

    def test_has_more_pages_false(self, appointment_list_data):
        """Test has_more_pages when no more pages."""
        appointment_list = AppointmentList(**appointment_list_data)
        assert appointment_list.has_more_pages is False

    def test_has_more_pages_true(self, appointment_list_data):
        """Test has_more_pages when more pages exist."""
        appointment_list_data["total_results"] = 100
        appointment_list = AppointmentList(**appointment_list_data)
        assert appointment_list.has_more_pages is True

    def test_next_start_index(self, appointment_list_data):
        """Test calculating next start index."""
        appointment_list = AppointmentList(**appointment_list_data)
        assert appointment_list.next_start_index == 50

    def test_active_appointments(self, appointment_list_data):
        """Test getting active appointments."""
        appointment_list = AppointmentList(**appointment_list_data)
        active = appointment_list.active_appointments
        assert len(active) == 1
        assert active[0].company_name == "Company A"

    def test_resigned_appointments(self, appointment_list_data):
        """Test getting resigned appointments."""
        appointment_list = AppointmentList(**appointment_list_data)
        resigned = appointment_list.resigned_appointments
        assert len(resigned) == 1
        assert resigned[0].company_name == "Company B"

    def test_empty_appointment_list(self):
        """Test creating an empty appointment list."""
        appointment_list = AppointmentList()
        assert appointment_list.items == []
        assert appointment_list.has_more_pages is False

    def test_appointment_list_with_date_of_birth(self, appointment_list_data):
        """Test appointment list with date of birth."""
        appointment_list_data["date_of_birth"] = {
            "month": 6,
            "year": 1970,
        }
        appointment_list = AppointmentList(**appointment_list_data)
        assert appointment_list.date_of_birth["month"] == 6
        assert appointment_list.date_of_birth["year"] == 1970


class TestCompanyStatus:
    """Test CompanyStatus enum."""

    def test_active_status(self):
        """Test active company status."""
        assert CompanyStatus.ACTIVE == "active"

    def test_dissolved_status(self):
        """Test dissolved company status."""
        assert CompanyStatus.DISSOLVED == "dissolved"

    def test_liquidation_status(self):
        """Test liquidation company status."""
        assert CompanyStatus.LIQUIDATION == "liquidation"

    def test_administration_status(self):
        """Test administration company status."""
        assert CompanyStatus.ADMINISTRATION == "administration"

    def test_all_status_values(self):
        """Test all company status values are unique."""
        statuses = [status.value for status in CompanyStatus]
        assert len(statuses) == len(set(statuses))
