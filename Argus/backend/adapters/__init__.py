from backend.adapters.angi_adapter import AngiAdapter
from backend.adapters.avvo_adapter import AvvoAdapter
from backend.adapters.bbb_adapter import BbbAdapter
from backend.adapters.facebook_adapter import FacebookAdapter
from backend.adapters.government_registry_adapter import GovernmentRegistryAdapter
from backend.adapters.healthgrades_adapter import HealthgradesAdapter
from backend.adapters.justdial_adapter import JustdialAdapter
from backend.adapters.linkedin_adapter import LinkedInAdapter
from backend.adapters.lybrate_adapter import LybrateAdapter
from backend.adapters.official_website_adapter import OfficialWebsiteAdapter
from backend.adapters.practo_adapter import PractoAdapter
from backend.adapters.professional_directory_adapter import ProfessionalDirectoryAdapter
from backend.adapters.sulekha_adapter import SulekhaAdapter
from backend.adapters.yellowpages_adapter import YellowPagesAdapter
from backend.adapters.yelp_adapter import YelpAdapter
from backend.adapters.zocdoc_adapter import ZocdocAdapter


def default_adapters():
    return [
        OfficialWebsiteAdapter(),
        YelpAdapter(),
        YellowPagesAdapter(),
        LinkedInAdapter(),
        FacebookAdapter(),
        JustdialAdapter(),
        SulekhaAdapter(),
        PractoAdapter(),
        LybrateAdapter(),
        HealthgradesAdapter(),
        ZocdocAdapter(),
        AvvoAdapter(),
        BbbAdapter(),
        AngiAdapter(),
        GovernmentRegistryAdapter(),
        ProfessionalDirectoryAdapter(),
    ]
