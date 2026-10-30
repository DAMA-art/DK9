from locust import HttpUser, task, TaskSet, SequentialTaskSet, between
from faker import Faker
import random

fake = Faker('ru_RU')

API = '/api'

def auth_headers(token: str) -> dict:
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

class AdminStaffTasks(TaskSet):
    access_token = None

    def on_start(self):
        with self.client.post(
            f'{API}/auth/login',
            json={'username': 'vet', 'password': 'vet12345!'},
            name='POST /auth/login (staff)',
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data['accessToken']
                resp.success()
            else:
                resp.failure(f'Login failed: {resp.status_code} {resp.text}')
#GET
    @task(5)
    def get_pets(self):
        params = {
            'page': random.randint(1, 3),
            'size': random.choice([5, 10, 20]),
        }
        if random.random() < 0.4:
            params['search'] = random.choice(
                ['Барсик', 'Рекс', 'кот', 'собака', 'CHIP']
            )
        if random.random() < 0.3:
            params['species'] = random.choice(['cat', 'dog'])
        self.client.get(
            f'{API}/pets',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /pets',
        )

    @task(5)
    def get_owners(self):
        params = {'page': 1, 'size': 10}
        if random.random() < 0.3:
            params['city'] = random.choice(
                ['Москва', 'Санкт-Петербург', 'Казань']
            )
        self.client.get(
            f'{API}/owners',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /owners',
        )

    @task(5)
    def get_clinics(self):
        self.client.get(
            f'{API}/clinics',
            params={'page': 1, 'size': 10},
            headers=auth_headers(self.access_token),
            name='GET /clinics',
        )

    @task(5)
    def get_services(self):
        params = {'page': 1, 'size': 10}
        if random.random() < 0.5:
            params['clinicId'] = random.randint(1, 3)
        self.client.get(
            f'{API}/services',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /services',
        )

    @task(3)
    def get_pet_by_id(self):
        pet_id = random.randint(1, 12)
        self.client.get(
            f'{API}/pets/{pet_id}',
            headers=auth_headers(self.access_token),
            name='GET /pets/{id}',
        )

    @task(3)
    def get_visits(self):
        self.client.get(
            f'{API}/visits',
            headers=auth_headers(self.access_token),
            name='GET /visits',
        )

    @task(2)
    def get_auth_me(self):
        self.client.get(
            f'{API}/auth/me',
            headers=auth_headers(self.access_token),
            name='GET /auth/me',
        )
#POST
    @task(1)
    def create_owner(self):
        payload = {
            'lastName': fake.last_name(),
            'firstName': fake.first_name(),
            'phone': fake.phone_number(),
            'email': fake.unique.email(),
            'city': fake.city_name(),
            'country': 'Россия',
        }
        with self.client.post(
            f'{API}/owners',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /owners',
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 422):
                resp.success()
            else:
                resp.failure(f'{resp.status_code}: {resp.text[:200]}')

    @task(1)
    def create_pet(self):
        species = random.choice(['cat', 'dog'])
        breeds = {
            'cat': [
                'Британский',
                'Сиамская',
                'Мейн-кун',
                'Персидская',
                'Дворняга',
            ],
            'dog': [
                'Лабрадор',
                'Хаски',
                'Корги',
                'Пудель',
                'Дворняга',
            ],
        }
        payload = {
            'name': fake.first_name(),
            'species': species,
            'breed': random.choice(breeds[species]),
            'chipNumber': f'CHIP-{fake.unique.random_int(min=10000, max=99999)}',
            'ageMonths': random.randint(1, 120),
            'weightKg': round(random.uniform(1.5, 40.0), 1),
            'clinicId': random.randint(1, 3),
            'ownerIds': [random.randint(1, 5)],
            'serviceIds': [random.randint(1, 5)],
            'notes': fake.sentence(nb_words=4) if random.random() < 0.3 else '',
        }
        with self.client.post(
            f'{API}/pets',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /pets',
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 422):
                resp.success()
            else:
                resp.failure(f'{resp.status_code}: {resp.text[:200]}')

    @task(1)
    def create_service(self):
        payload = {
            'name': random.choice(
                [
                    'Стрижка',
                    'Мытьё',
                    'Чистка зубов',
                    'SPA',
                    'Вычёсывание',
                    'Стрижка когтей',
                ]
            ),
            'description': fake.sentence(nb_words=6),
            'price': random.randint(300, 5000),
            'clinicId': random.randint(1, 3),
        }
        with self.client.post(
            f'{API}/services',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /services',
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 422):
                resp.success()
            else:
                resp.failure(f'{resp.status_code}: {resp.text[:200]}')


class ClientScenario(SequentialTaskSet):
    access_token = None

    @task
    def login_as_client(self):
        with self.client.post(
            f'{API}/auth/login',
            json={'username': 'client', 'password': 'client12!'},
            name='POST /auth/login (client)',
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.access_token = resp.json()['accessToken']
                resp.success()
            else:
                resp.failure(f'Client login failed: {resp.status_code}')

    @task
    def get_me(self):
        if not self.access_token:
            return
        self.client.get(
            f'{API}/auth/me',
            headers=auth_headers(self.access_token),
            name='GET /auth/me (client)',
        )

    @task
    def list_visits(self):
        if not self.access_token:
            return
        self.client.get(
            f'{API}/visits',
            headers=auth_headers(self.access_token),
            name='GET /visits (client)',
        )

    @task
    def try_extend_visit(self):
        if not self.access_token:
            return
        with self.client.post(
            f'{API}/visits/1/extend',
            json={'days': random.randint(1, 5)},
            headers=auth_headers(self.access_token),
            name='POST /visits/{id}/extend',
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404, 409):
                resp.success()
            else:
                resp.failure(f'{resp.status_code}: {resp.text[:150]}')


class ZooUser(HttpUser):
    host = 'http://127.0.0.1:8000'
    wait_time = between(0.5, 1.5)
    tasks = {
        AdminStaffTasks: 4,
        ClientScenario: 1,
    }