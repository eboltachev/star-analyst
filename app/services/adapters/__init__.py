from app.services.adapters.fns import FnsRegistryAdapter
from app.services.adapters.sudrf import SudrfAdapter
from app.services.adapters.mvd import MvdWantedAdapter

ADAPTERS = {
    "FnsRegistryAdapter": FnsRegistryAdapter,
    "SudrfAdapter": SudrfAdapter,
    "MvdWantedAdapter": MvdWantedAdapter,
}
