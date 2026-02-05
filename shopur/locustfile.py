from locust import HttpUser, task, constant_throughput, SequentialTaskSet, TaskSet
from faker import Faker

fake = Faker("ru_RU")


class UserFlow(SequentialTaskSet):

    @task
    def open_home(self):
        self.client.get("/")

    @task
    def open_catalog(self):
        self.client.get("/catalog/")

    @task
    def open_profile(self):
        self.client.get("/profile/")


class RandomAct(TaskSet):
    def on_start(self):
        response = self.client.get("/login/")
        self.csrf_token = response.cookies.get("csrftoken")

        self.client.post(
            "/login/",
            data={
                "username": "Liza",
                "password": "Cockepinle1",
                "csrfmiddlewaretoken": self.csrf_token,
            }
        )

    @task(5)
    def get_products(self):
        self.client.get("/api/products/")

    @task(5)
    def get_product_detail(self):
        self.client.get(f"/api/products/3/")

    @task(1)
    def create_order(self): 
        self.client.post( "/api/orders/",
            json={
                "user": 20,
                "status": 1,
                "address_delivery": "address",
                "total_amount": "1000.00"
            })

    @task(1)
    def update_user_name(self):
        self.client.put(
            "/api/users/20/",
            json={
                "username": fake.user_name(),
                "email": "liza@example.com",
                "first_name": "Liza",
                "last_name": "Ivanova"
            })

class WebsiteUser(HttpUser):
    wait_time = constant_throughput(5)
    tasks = [UserFlow, RandomAct]

    
