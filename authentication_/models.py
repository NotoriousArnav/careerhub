from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
import uuid

# Create your models here.
class Company(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    logo = models.ImageField(upload_to="", blank=True, null=True)
    name = models.CharField(default="Wayne Enterprises", max_length=200)
    description = models.TextField(default="""Wayne Enterprises is one of the largest conglomerates in world history with operations in aerospace, technology, biotech, shipping, shipbuilding, foods, medicine, electronics, entertainment, alternative energy, steel, chemicals, and philanthropy.

The colossal organization was founded by Solomon Wayne in the late 17th century, who turned a modest real estate fortune left by his father Charles' estate, into a merchant house. Leveraging his earned status as a prominent Gotham citizen, he grew the company rapidly in the late 1850s and his son Alan Wayne led the breakthrough, incorporating Gotham Railroads, Wayne Shipping, Wayne Chemicals, and Wayne Manufacturing, laying the cement for the diverse powerhouse Wayne Enterprises is today. Alan Wayne's grandson Patrick Morgan Wayne developed WayneTech, one of the most important divisions of the Enterprises, out of the ashes of the Great Depression, whose aircraft and naval technologies fueled the American efforts in the Pacific theater of World War II. 
Mr. Patrick Wayne's son, Dr. Thomas Wayne, turned the direction of the company to its current prominence in social responsibility, starting the charitable Wayne Foundation. Following Dr. Wayne's shocking murder, the company's board of directors took the ailing company public in a controversial decision. 

Today, Wayne Enterprises is led by Lucius Fox, appointed by playboy billionaire heir Bruce Wayne, whose estate owns a majority stake through various trusts and charities. In 2012, Wayne Enterprises was targeted by an underground guerilla group that defrauded Wayne Enterprises' stock price through deliberate market manipulation. Mr. Wayne went missing following the Gotham nuclear scare but rumors speculate he's alive in Italy and bound to return to his post.""")
    registration = models.DateField(auto_now_add=True, editable=True)

    def __str__(self):
        return f'{self.name}'

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pfp = models.ImageField(upload_to="", blank=True, null=True)
    bio = models.TextField(default="""Hi, I love CareerHub""")
    is_recruiter = models.BooleanField(default=False)
    firstlogin = models.BooleanField(default=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, null=True, blank=True)
    resume_json = models.TextField(default={})

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s profile"

def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
        profile, created = UserProfile.objects.get_or_create(user=instance)



post_save.connect(create_user_profile, sender=User)
