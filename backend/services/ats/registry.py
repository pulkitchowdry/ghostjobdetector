from .smartrecruiters import SmartRecruitersAdapter
from .greenhouse import GreenhouseAdapter

ATS_REGISTRY = {
    "smartrecruiters"   :   SmartRecruitersAdapter(),
    "greenhouse"        :   GreenhouseAdapter(),
}
