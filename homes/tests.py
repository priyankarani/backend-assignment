import json

from django.test import TestCase, Client
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.core.exceptions import ValidationError

from homes.models import House, Room, Light, Thermostat, TrackRecord
from homes.admin import CustomListFilter, TrackRecordAdmin

client = Client()


class TestMixin(TestCase):

    def create_and_login_new_user(
        self, login=True, username='newuser',
        email='user@example.com',
    ):
        """
        Create a new user and login
        :param login: Boolean to specify if the user must be logged in or not
        """
        User = get_user_model()

        user = User.objects.create(email=email)
        user.set_password("password")

        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        if login:
            client.force_login(user)
            user = auth.get_user(client)
            assert user.is_authenticated
        return user

    def logout(self):
        """
        Helper method to logout user
        """
        response = client.get('/api/logout/')
        self.assertEqual(response.status_code, 200)
        return response


class TestHouse(TestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestHouse, cls).setUpClass()

        cls.house1 = House.objects.create(name="Test House1")
        cls.house2 = House.objects.create(name="Test House2")

    def test_0010_test_house_api(self):
        """
        Check read access for house api
        """

        # Check api without login
        response = client.get('/api/houses/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        response = client.get('/api/houses/%d/' % self.house1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.get('/api/houses/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = client.get('/api/houses/%d/' % self.house1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.house1.id)
        self.assertFalse(response.data["thermostats"])
        self.assertFalse(response.data["rooms"])

        # Create room and thermostat for this house and check if house api
        # returns that info too
        room = Room.objects.create(
            name="Test Room1", house=self.house1,
            current_temperature=33,
        )
        thermo = Thermostat.objects.create(
            name="Thermo",
            house=self.house1,
            mode="auto",
            current_temperature=40,
            temperature_set_point=55,
        )
        response = client.get('/api/houses/%d/' % self.house1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.house1.id)
        self.assertEqual(len(response.data["thermostats"]), 1)
        self.assertEqual(len(response.data["rooms"]), 1)
        self.assertTrue(room.id in response.data["rooms"])
        self.assertTrue(thermo.id in response.data["thermostats"])

    def test_0020_test_create_house_api(self):
        """
        Check house api to create houses
        """
        self.assertEqual(House.objects.all().count(), 2)
        # Check api without login
        response = client.post(
            '/api/houses/', content_type='application/json',
            data=json.dumps({
                'name': 'Test House'
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(House.objects.all().count(), 2)

        # Check with login
        self.create_and_login_new_user()

        response = client.post(
            '/api/houses/', content_type='application/json',
            data=json.dumps({
                'name': 'Test House'
            })
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Test House")
        self.assertEqual(House.objects.all().count(), 3)

        self.assertEqual(
            str(House.objects.get(id=response.data["id"])), "Test House"
        )

    def test_0030_test_update_house_api(self):
        """
        Check house api to update houses
        """
        # Check api without login
        response = client.put(
            '/api/houses/%d/' % self.house1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New House'
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.put(
            '/api/houses/%d/' % self.house1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New House'
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "New House")

        self.assertEqual(House.objects.get(id=self.house1.id).name, "New House")

    def test_0040_test_delete_house_api(self):
        """
        Check house api to delete houses
        """
        self.assertEqual(House.objects.all().count(), 2)

        # Try deleting without login
        response = client.delete('/api/houses/%d/' % self.house1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(House.objects.all().count(), 2)

        # Login and try to delete
        self.create_and_login_new_user()
        response = client.delete('/api/houses/%d/' % self.house1.id)
        self.assertEqual(response.status_code, 204)

        self.assertEqual(House.objects.all().count(), 1)


class TestRoom(TestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestRoom, cls).setUpClass()

        cls.house1 = House.objects.create(name="Test House1")
        cls.house2 = House.objects.create(name="Test House2")

        cls.room1 = Room.objects.create(
            name="Test Room1", house=cls.house1,
            current_temperature=33,
        )
        cls.room2 = Room.objects.create(
            name="Test Room2", house=cls.house2,
            current_temperature=35,
        )

    def test_0010_test_room_api(self):
        """
        Check read access for room api
        """

        # Check api without login
        response = client.get('/api/rooms/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        response = client.get('/api/rooms/%d/' % self.room1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.get('/api/rooms/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = client.get('/api/rooms/%d/' % self.room1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.room1.id)
        self.assertFalse(response.data["lights"])

        # Create light for this room and check if room api returns light
        # info too
        light = Light.objects.create(
            name="Test Light",
            state="on",
            room=self.room1
        )
        response = client.get('/api/rooms/%d/' % self.room1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.room1.id)
        self.assertEqual(len(response.data["lights"]), 1)
        self.assertTrue(light.id in response.data["lights"])

    def test_0020_test_create_room_api(self):
        """
        Check room api to create rooms
        """
        self.assertEqual(Room.objects.all().count(), 2)

        # Check api without login
        response = client.post(
            '/api/rooms/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Room',
                'current_temperature': 30,
                "house": self.house1.id
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        self.assertEqual(Room.objects.all().count(), 2)

        # Check with login
        self.create_and_login_new_user()

        response = client.post(
            '/api/rooms/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Room',
                'current_temperature': 30,
                "house": self.house1.id
            })
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Test Room")

        self.assertEqual(Room.objects.all().count(), 3)

        self.assertEqual(
            str(Room.objects.get(id=response.data["id"])), "Test Room"
        )

    def test_0030_test_update_room_api(self):
        """
        Check api to update rooms
        """

        # Check api without login
        response = client.put(
            '/api/rooms/%d/' % self.room1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New Room',
                'current_temperature': 30,
                'house': self.house1.id
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.put(
            '/api/rooms/%d/' % self.room1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New Room',
                'current_temperature': 30,
                'house': self.house1.id,
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "New Room")

        self.assertEqual(Room.objects.get(id=self.room1.id).name, "New Room")

    def test_0040_test_delete_room_api(self):
        """
        Check room api to delete rooms
        """
        TrackRecord.objects.create(
            name=self.room1.name,
            target_content_type=ContentType.objects.get_for_model(Room),
            target_object_id=self.room1.id,
            from_state=30,
            to_state=40,
            state_type="Temperature",
        )
        self.assertEqual(Room.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Try deleting without login
        response = client.delete('/api/rooms/%d/' % self.room1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(Room.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Login and try to delete
        self.create_and_login_new_user()

        response = client.delete('/api/rooms/%d/' % self.room1.id)

        self.assertEqual(Room.objects.all().count(), 1)

        # Deletes related track record too
        self.assertEqual(TrackRecord.objects.all().count(), 0)


class TestLight(TestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestLight, cls).setUpClass()

        cls.house1 = House.objects.create(name="Test House1")
        cls.house2 = House.objects.create(name="Test House2")

        cls.room1 = Room.objects.create(
            name="Test Room1", house=cls.house1,
            current_temperature=33,
        )
        cls.room2 = Room.objects.create(
            name="Test Room2", house=cls.house2,
            current_temperature=35,
        )

        cls.light1 = Light.objects.create(
            name="Test Light1",
            state="on",
            room=cls.room1
        )

        cls.light2 = Light.objects.create(
            name="Test Light2",
            state="off",
            room=cls.room2
        )

    def test_0010_test_light_api(self):
        """
        Check api to read light data
        """
        # Check api without login
        response = client.get('/api/lights/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        response = client.get('/api/lights/%d/' % self.light1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.get('/api/lights/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = client.get('/api/lights/%d/' % self.light1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.light1.id)

    def test_0020_test_create_light_api(self):
        """
        Check api to create light
        """
        self.assertEqual(Light.objects.all().count(), 2)

        # Check api without login
        response = client.post(
            '/api/lights/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Light',
                'state': "on",
                "room": self.room1.id
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        self.assertEqual(Light.objects.all().count(), 2)

        # Check with login
        self.create_and_login_new_user()

        response = client.post(
            '/api/lights/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Light',
                'state': "on",
                "room": self.room1.id
            })
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Test Light")

        self.assertEqual(Light.objects.all().count(), 3)

        self.assertEqual(
            str(Light.objects.get(id=response.data["id"])), "Test Light"
        )

    def test_0030_test_update_light_api(self):
        """
        Check api to update lights
        """

        # Check api without login
        response = client.put(
            '/api/lights/%d/' % self.light1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New Light',
                'state': 'on',
                'room': self.room1.id,
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.put(
            '/api/lights/%d/' % self.light1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New Light',
                'state': 'on',
                'room': self.room1.id,
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "New Light")

        self.assertEqual(Light.objects.get(id=self.light1.id).name, "New Light")

    def test_0040_test_delete_light_api(self):
        """
        Check light api to delete lights
        """
        TrackRecord.objects.create(
            name=self.light1.name,
            target_content_type=ContentType.objects.get_for_model(Light),
            target_object_id=self.light1.id,
            from_state="on",
            to_state="off",
            state_type="State",
        )
        self.assertEqual(Light.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Try deleting without login
        response = client.delete('/api/lights/%d/' % self.light1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(Light.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Login and try to delete
        self.create_and_login_new_user()

        response = client.delete('/api/lights/%d/' % self.light1.id)
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Light.objects.all().count(), 1)

        # Deletes related track record too
        self.assertEqual(TrackRecord.objects.all().count(), 0)


class TestThermostat(TestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestThermostat, cls).setUpClass()

        cls.house1 = House.objects.create(name="Test House1")
        cls.house2 = House.objects.create(name="Test House2")

        cls.thermostat1 = Thermostat.objects.create(
            name="Thermo1",
            house=cls.house1,
            mode="cool",
            current_temperature=30,
            temperature_set_point=45,
        )
        cls.thermostat2 = Thermostat.objects.create(
            name="Thermo2",
            house=cls.house2,
            mode="auto",
            current_temperature=40,
            temperature_set_point=55,
        )

    def test_0010_test_thermostat_api(self):
        """
        Check api to read thermostat data
        """
        # Check api without login
        response = client.get('/api/thermostats/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        response = client.get('/api/thermostats/%d/' % self.thermostat1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.get('/api/thermostats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = client.get('/api/thermostats/%d/' % self.thermostat1.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.thermostat1.id)

    def test_0020_test_create_thermostat_api(self):
        """
        Check api to create thermostat
        """

        self.assertEqual(Thermostat.objects.all().count(), 2)

        # Check api without login
        response = client.post(
            '/api/thermostats/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Thermo',
                'mode': 'auto',
                'current_temperature': 35,
                'temperature_set_point': 40,
                'house': self.house1.id,
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        self.assertEqual(Thermostat.objects.all().count(), 2)

        # Check with login
        self.create_and_login_new_user()

        response = client.post(
            '/api/thermostats/', content_type='application/json',
            data=json.dumps({
                'name': 'Test Thermo',
                'mode': 'auto',
                'current_temperature': 35,
                'temperature_set_point': 40,
                'house': self.house1.id,
            })
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Test Thermo")

        self.assertEqual(Thermostat.objects.all().count(), 3)

        self.assertEqual(
            str(Thermostat.objects.get(id=response.data["id"])),
            "Test Thermo"
        )

    def test_0030_test_update_thermostat_api(self):
        """
        Check api to update thermostats
        """

        # Check api without login
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': 'New Thermo',
                'mode': 'auto',
                'current_temperature': 35,
                'temperature_set_point': 40,
                'house': self.house1.id,
            })
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )

        # Check with login
        self.create_and_login_new_user()

        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': 'New Thermo',
                'mode': 'auto',
                'current_temperature': 35,
                'temperature_set_point': 40,
                'house': self.house1.id,
            })
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "New Thermo")

        self.assertEqual(
            Thermostat.objects.get(id=self.thermostat1.id).name, "New Thermo"
        )

    def test_0040_test_delete_thermostat_api(self):
        """
        Check api to delete thermostat
        """
        TrackRecord.objects.create(
            name=self.thermostat1.name,
            target_content_type=ContentType.objects.get_for_model(Thermostat),
            target_object_id=self.thermostat1.id,
            from_state=30,
            to_state=20,
            state_type="Temperature",
        )
        self.assertEqual(Thermostat.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Try deleting without login
        response = client.delete('/api/thermostats/%d/' % self.thermostat1.id)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data["detail"],
            "Authentication credentials were not provided."
        )
        self.assertEqual(Thermostat.objects.all().count(), 2)
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        # Login and try to delete
        self.create_and_login_new_user()

        response = client.delete('/api/thermostats/%d/' % self.thermostat1.id)
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Thermostat.objects.all().count(), 1)
        self.assertEqual(TrackRecord.objects.all().count(), 0)


class TestTrackRecord(TestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestTrackRecord, cls).setUpClass()

        cls.house1 = House.objects.create(name="Test House1")
        cls.house2 = House.objects.create(name="Test House2")

        cls.room1 = Room.objects.create(
            name="Test Room1", house=cls.house1,
            current_temperature=33,
        )
        cls.room2 = Room.objects.create(
            name="Test Room2", house=cls.house2,
            current_temperature=35,
        )

        cls.light1 = Light.objects.create(
            name="Test Light1",
            state="on",
            room=cls.room1
        )

        cls.light2 = Light.objects.create(
            name="Test Light2",
            state="off",
            room=cls.room2
        )

        cls.thermostat1 = Thermostat.objects.create(
            name="Thermo1",
            house=cls.house1,
            mode="cool",
            current_temperature=30,
            temperature_set_point=45,
        )
        cls.thermostat2 = Thermostat.objects.create(
            name="Thermo2",
            house=cls.house2,
            mode="auto",
            current_temperature=40,
            temperature_set_point=55,
        )

    def test_0010_check_track_records_thermostat_case_1(self):
        """
        Check track records for thermostat when only name or house is changed
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # 1. Change name and house and no track record should be created
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': 'New Thermo',
                'mode': self.thermostat1.mode,
                'current_temperature': self.thermostat1.current_temperature,
                'temperature_set_point': self.thermostat1.temperature_set_point,
                'house': self.house2.id,
            })
        )
        self.assertEqual(response.status_code, 200)

        thermostat = Thermostat.objects.get(id=self.thermostat1.id)

        self.assertEqual(
            thermostat.mode, self.thermostat1.mode
        )
        self.assertEqual(
            thermostat.current_temperature,
            self.thermostat1.current_temperature
        )
        self.assertEqual(
            thermostat.temperature_set_point,
            self.thermostat1.temperature_set_point
        )
        self.assertNotEqual(
            thermostat.name, self.thermostat1.name
        )
        self.assertNotEqual(
            thermostat.house.id, self.thermostat1.house.id
        )

        # Track Record has not been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 0)

    def test_0020_check_track_records_thermostat_case_2(self):
        """
        Check track records for thermostat when mode is changed
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # Change only mode and track record should be created
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': self.thermostat1.name,
                'mode': "off",
                'current_temperature': self.thermostat1.current_temperature,
                'temperature_set_point': self.thermostat1.temperature_set_point,
                'house': self.thermostat1.house.id,
            })
        )
        self.assertEqual(response.status_code, 200)

        thermostat = Thermostat.objects.get(id=self.thermostat1.id)

        self.assertNotEqual(
            thermostat.mode, self.thermostat1.mode
        )
        self.assertEqual(
            thermostat.current_temperature,
            self.thermostat1.current_temperature
        )
        self.assertEqual(
            thermostat.temperature_set_point,
            self.thermostat1.temperature_set_point
        )
        self.assertEqual(
            thermostat.name, self.thermostat1.name
        )
        self.assertEqual(
            thermostat.house.id, self.thermostat1.house.id
        )

        # Track Record has been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 1)
        self.assertTrue(
            "[Thermo1] Mode has been changed from cool to off" in
            str(TrackRecord.objects.all()[0])
        )

    def test_0030_check_track_records_thermostat_case_3(self):
        """
        Check track records for thermostat when mode is changed
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # Change only current temperature and track record should be created
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': self.thermostat1.name,
                'mode': self.thermostat1.mode,
                'current_temperature': 77,
                'temperature_set_point': self.thermostat1.temperature_set_point,
                'house': self.thermostat1.house.id,
            })
        )
        self.assertEqual(response.status_code, 200)

        thermostat = Thermostat.objects.get(id=self.thermostat1.id)

        self.assertEqual(
            thermostat.mode, self.thermostat1.mode
        )
        self.assertNotEqual(
            thermostat.current_temperature,
            self.thermostat1.current_temperature
        )
        self.assertEqual(
            thermostat.temperature_set_point,
            self.thermostat1.temperature_set_point
        )
        self.assertEqual(
            thermostat.name, self.thermostat1.name
        )
        self.assertEqual(
            thermostat.house.id, self.thermostat1.house.id
        )

        # Track Record has been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 1)
        self.assertTrue(
            "[Thermo1] Temperature has been changed from 30.00 to 77.00" in
            str(TrackRecord.objects.all()[0])
        )

    def test_0040_check_track_records_thermostat_case_4(self):
        """
        Check track records for thermostat when temperature set point is changed
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # 3. Change only temperature set point and track record should
        # be created
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': self.thermostat1.name,
                'mode': self.thermostat1.mode,
                'current_temperature': self.thermostat1.current_temperature,
                'temperature_set_point': 78,
                'house': self.thermostat1.house.id,
            })
        )
        self.assertEqual(response.status_code, 200)

        thermostat = Thermostat.objects.get(id=self.thermostat1.id)

        self.assertEqual(
            thermostat.mode, self.thermostat1.mode
        )
        self.assertEqual(
            thermostat.current_temperature,
            self.thermostat1.current_temperature
        )
        self.assertNotEqual(
            thermostat.temperature_set_point,
            self.thermostat1.temperature_set_point
        )
        self.assertEqual(
            thermostat.name, self.thermostat1.name
        )
        self.assertEqual(
            thermostat.house.id, self.thermostat1.house.id
        )

        # Track Record has been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 1)
        self.assertTrue(
            "[Thermo1] Temperature set point has been changed from 45.00 "
            "to 78.00" in
            str(TrackRecord.objects.all()[0])
        )

    def test_0050_check_track_records_thermostat_case_5(self):
        """
        Check track records for thermostat when mode, temperature and set point
        are changed all at once
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # Change mode, temperature and set point all at once and 3 track
        # records should be created
        response = client.put(
            '/api/thermostats/%d/' % self.thermostat1.id,
            content_type='application/json',
            data=json.dumps({
                'name': self.thermostat1.name,
                'mode': "fan",
                'current_temperature': 66,
                'temperature_set_point': 89,
                'house': self.thermostat1.house.id,
            })
        )
        self.assertEqual(response.status_code, 200)

        thermostat = Thermostat.objects.get(id=self.thermostat1.id)

        self.assertNotEqual(
            thermostat.mode, self.thermostat1.mode
        )
        self.assertNotEqual(
            thermostat.current_temperature,
            self.thermostat1.current_temperature
        )
        self.assertNotEqual(
            thermostat.temperature_set_point,
            self.thermostat1.temperature_set_point
        )
        self.assertEqual(
            thermostat.name, self.thermostat1.name
        )
        self.assertEqual(
            thermostat.house.id, self.thermostat1.house.id
        )

        # Track Record has been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 3)

        self.assertTrue(
            "[Thermo1] Temperature set point has been changed from 45.00 "
            "to 89.00" in
            str(TrackRecord.objects.filter(
                state_type="Temperature set point"
            )[0])
        )
        self.assertTrue(
            "[Thermo1] Temperature has been changed from 30.00 to 66.00" in
            str(TrackRecord.objects.filter(state_type="Temperature")[0])
        )
        self.assertTrue(
            "[Thermo1] Mode has been changed from cool to fan "
            in str(TrackRecord.objects.filter(state_type="Mode")[0])
        )

    def test_0060_check_track_records_light_case_1(self):
        """
        Check track records for light when only name or room is chnaged
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # Change name and room and no track record should be created
        response = client.put(
            '/api/lights/%d/' % self.light1.id, content_type='application/json',
            data=json.dumps({
                'name': "new light",
                'state': self.light1.state,
                'room': self.room2.id,
            })
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            Light.objects.get(id=self.light1.id).state, self.light1.state
        )
        self.assertNotEqual(
            Light.objects.get(id=self.light1.id).name, self.light1.name
        )
        self.assertNotEqual(
            Light.objects.get(id=self.light1.id).room.id, self.light1.room.id
        )

        # Track Record has not been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 0)

    def test_0070_check_track_records_light_case_2(self):
        """
        Check track records for light when only name or room is chnaged
        """
        self.create_and_login_new_user()

        self.assertEqual(self.light1.state, "on")
        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # Change state of light on to off
        response = client.put(
            '/api/lights/%d/' % self.light1.id, content_type='application/json',
            data=json.dumps({
                'name': self.light1.name,
                'state': "off",
                'room': self.light1.room.id,
            })
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotEqual(
            Light.objects.get(id=self.light1.id).state, self.light1.state
        )
        self.assertEqual(
            Light.objects.get(id=self.light1.id).name, self.light1.name
        )
        self.assertEqual(
            Light.objects.get(id=self.light1.id).room.id, self.light1.room.id
        )

        # Track Record has been created for the change
        self.assertEqual(TrackRecord.objects.all().count(), 1)

        self.assertTrue(
            "[Test Light1] State has been changed from on to off" in
            str(TrackRecord.objects.all()[0])
        )

    def test_0080_check_track_records_room_case_1(self):
        """
        Check track records for room when only name and house is changed
        """
        self.create_and_login_new_user()

        self.assertEqual(TrackRecord.objects.all().count(), 0)

        # 1. Try changing name and house and no track record will be
        # created
        response = client.put(
            '/api/rooms/%d/' % self.room1.id, content_type='application/json',
            data=json.dumps({
                'name': 'New Room',
                'current_temperature': self.room1.current_temperature,
                'house': self.house2.id,
            })
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotEqual(
            Room.objects.get(id=self.room1.id).name, self.room1.name
        )
        self.assertNotEqual(
            Room.objects.get(id=self.room1.id).house.id, self.room1.house.id
        )
        self.assertEqual(
            Room.objects.get(id=self.room1.id).current_temperature,
            self.room1.current_temperature
        )

        # Track Record has not been created for above change
        self.assertEqual(TrackRecord.objects.all().count(), 0)

    def test_0090_check_track_records_room_case_2(self):
        """
        Check track records for room when only room temperature is changed
        """
        self.create_and_login_new_user()

        # 2. Change current temperature and track record should be created
        response = client.put(
            '/api/rooms/%d/' % self.room1.id, content_type='application/json',
            data=json.dumps({
                'name': self.room1.name,
                'current_temperature': 40,
                'house': self.room1.house.id,
            })
        )

        self.assertEqual(response.status_code, 200)

        self.assertNotEqual(
            Room.objects.get(id=self.room1.id).current_temperature,
            self.room1.current_temperature
        )
        self.assertEqual(
            Room.objects.get(id=self.room1.id).name, self.room1.name
        )
        self.assertEqual(
            Room.objects.get(id=self.room1.id).house.id, self.room1.house.id
        )

        # Track Record has been created for the change
        self.assertEqual(TrackRecord.objects.all().count(), 1)
        self.assertTrue(
            "[Test Room1] Temperature has been changed from 33.00 to 40.00" in
            str(TrackRecord.objects.all()[0])
        )

    def test_0100_check_track_record_validation(self):
        """
        Check validation when target id does not exist for target object
        """
        with self.assertRaises(ValidationError) as e:
            TrackRecord.objects.create(
                name="Track Room",
                target_content_type=ContentType.objects.get_for_model(Room),
                target_object_id=10,
                from_state="on",
                to_state="off",
                state_type="State",
            )
        self.assertTrue(
            'room with id 10 does not exist!' in str(e.exception)
        )

    def test_0110_check_custom_admin_filter(self):
        """
        Check admin filter for track record that filters track records based
        on type of equipments
        """

        track_room = TrackRecord.objects.create(
            name=self.room1.name,
            target_content_type=ContentType.objects.get_for_model(Room),
            target_object_id=self.room1.id,
            from_state=30,
            to_state=40,
            state_type="Temperature",
        )

        track_light = TrackRecord.objects.create(
            name=self.light1.name,
            target_content_type=ContentType.objects.get_for_model(Light),
            target_object_id=self.light1.id,
            from_state="on",
            to_state="off",
            state_type="State",
        )

        track_thermostat = TrackRecord.objects.create(
            name=self.thermostat1.name,
            target_content_type=ContentType.objects.get_for_model(Thermostat),
            target_object_id=self.thermostat1.id,
            from_state=30,
            to_state=20,
            state_type="Temperature",
        )

        # Filter for light
        filter = CustomListFilter(
            None, {'equipments': 'Light'}, TrackRecord, TrackRecordAdmin
        )

        results = filter.queryset(None, TrackRecord.objects.all())

        self.assertEqual(results.count(), 1)
        self.assertEqual(
            results[0].target_content_type,
            ContentType.objects.get_for_model(Light)
        )
        self.assertEqual(results[0].target_object_id, self.light1.id)
        self.assertEqual(results[0].name, "Test Light1")
        self.assertEqual(results[0].id, track_light.id)

        # Filter for room
        filter = CustomListFilter(
            None, {'equipments': 'Room'}, TrackRecord, TrackRecordAdmin
        )

        results = filter.queryset(None, TrackRecord.objects.all())

        self.assertEqual(results.count(), 1)
        self.assertEqual(
            results[0].target_content_type,
            ContentType.objects.get_for_model(Room)
        )
        self.assertEqual(results[0].target_object_id, self.room1.id)
        self.assertEqual(results[0].name, "Test Room1")
        self.assertEqual(results[0].id, track_room.id)

        # Filter for thermostat
        filter = CustomListFilter(
            None, {'equipments': 'Thermostat'}, TrackRecord, TrackRecordAdmin
        )

        results = filter.queryset(None, TrackRecord.objects.all())

        self.assertEqual(results.count(), 1)
        self.assertEqual(
            results[0].target_content_type,
            ContentType.objects.get_for_model(Thermostat)
        )
        self.assertEqual(results[0].target_object_id, self.thermostat1.id)
        self.assertEqual(results[0].name, "Thermo1")
        self.assertEqual(results[0].id, track_thermostat.id)

        # Filter without any value and it will return all 3 track records
        filter = CustomListFilter(
            None, {'equipments': None}, TrackRecord, TrackRecordAdmin
        )

        results = filter.queryset(None, TrackRecord.objects.all())

        self.assertEqual(results.count(), 3)
