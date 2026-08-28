"""Central, presentation-only configuration for the showcase."""

from dataclasses import dataclass
from pathlib import Path


SHOWCASE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SHOWCASE_ROOT.parent
COMPONENT2_ROOT = (
    PROJECT_ROOT / "components" / "component_2_right_of_way_negotiation"
)
HOST = "127.0.0.1"
PORT = 8088
PROJECT_TITLE = "SOCIALMIND DRIVE"
PROJECT_SUBTITLE = "Agentic AI for Robust and Socially-Aware Autonomous Driving"
PROJECT_DESCRIPTION = (
    "An agentic autonomous-driving research initiative exploring how intelligent "
    "vehicles can perceive uncertain environments, negotiate shared road space, "
    "reason about social behavior, and collaboratively share knowledge."
)
SHOWCASE_NOTE = (
    "This platform provides a common presentation layer for the four SOCIALMIND "
    "DRIVE research components. Component 2 is currently integrated for live "
    "local execution, while the remaining research components have reserved "
    "presentation and runtime integration spaces."
)


@dataclass(frozen=True)
class Component:
    slug: str
    number: str
    pillar: str
    title: str
    description: str
    category: str
    labels: tuple[str, ...]
    status: str
    icon: str
    image_name: str
    live: bool = False
    launch_command: tuple[str, ...] | None = None
    working_directory: Path | None = None
    result_path: Path | None = None


@dataclass(frozen=True)
class Person:
    name: str
    display_order: int
    role: str
    department: str
    institution: str
    location: str
    email: str
    image_name: str


COMPONENTS = (
    Component(
        "adaptive-intent", "01", "UNDERSTAND INTENT",
        "Adaptive Intent Prediction in Occluded Urban Scenarios",
        "Researches robust inference of vehicle intent when observations are "
        "incomplete or partially occluded in complex urban driving conditions.",
        "Perception & Intent", ("Intent Prediction", "Occlusion Handling", "Urban Perception"),
        "PRESENTATION SPACE RESERVED", "visibility", "component_1.jpg"),
    Component(
        "right-of-way", "02", "NEGOTIATE SHARED SPACE",
        "Multi-Agent Negotiation for Right-of-Way in Complex Intersections",
        "Develops decentralized right-of-way negotiation for autonomous vehicles "
        "at complex unsignalized intersections using local perception, traffic-rule "
        "precedence, graph reasoning and MAPPO.",
        "Multi-Agent Coordination", ("Multi-Agent Systems", "MAPPO", "Right-of-Way", "SUMO"),
        "LIVE DEMO AVAILABLE", "hub", "component_2.png", True,
        ("{python}", "run_panel_demo.py", "--gui", "--gui-delay-ms", "10"),
        COMPONENT2_ROOT,
        COMPONENT2_ROOT / "results" / "panel_demo" / "latest_panel_demo.json"),
    Component(
        "social-compliance", "03", "REASON SOCIALLY",
        "Proactive Social Compliance Modeling using Agentic Theory of Mind",
        "Explores socially aware autonomous-driving reasoning by modeling and "
        "anticipating the behavior, expectations and likely responses of other road users.",
        "Social Intelligence", ("Theory of Mind", "Social Reasoning", "Agentic AI"),
        "PRESENTATION SPACE RESERVED", "psychology", "component_3.png"),
    Component(
        "federated-learning", "04", "LEARN COLLECTIVELY",
        "Federated Collective Learning Between Autonomous Vehicles using Agentic Knowledge Sharing",
        "Explores collaborative learning between autonomous vehicles through "
        "decentralized knowledge sharing while retaining local learning and data ownership.",
        "Collective Learning", ("Federated Learning", "Knowledge Sharing", "Collaborative AVs"),
        "PRESENTATION SPACE RESERVED", "device_hub", "component_4.png"),
)
COMPONENT_BY_SLUG = {item.slug: item for item in COMPONENTS}
COMPONENT2 = COMPONENT_BY_SLUG["right-of-way"]

HOME_HERO_IMAGE = SHOWCASE_ROOT / "assets" / "images" / "home_page.png"
RESEARCH_VISION_IMAGE = SHOWCASE_ROOT / "assets" / "images" / "socialmind_hero.jpg"
BRAND_LOGO_IMAGE = SHOWCASE_ROOT / "assets" / "logos" / "socialmind_logo.png"
INSTITUTION_LOGO_IMAGE = SHOWCASE_ROOT / "assets" / "logos" / "sliit_logo.png"
TEAM_ASSET_ROOT = SHOWCASE_ROOT / "assets" / "team"
INSTITUTION_NAME = "Sri Lanka Institute of Information Technology (SLIIT)"
FACULTY_NAME = "Faculty of Computing"
INSTITUTION_LOCATION = "Malabe, Sri Lanka"

TEAM_MEMBERS = (
    Person("Avishka Piyumal", 1, "Research Team Member",
           "Department of Computer Science", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "it22245960@my.sliit.lk", "avishka_piyumal.jpg"),
    Person("Iresha Nethmini", 2, "Research Team Member",
           "Department of Computer Science", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "it22265906@my.sliit.lk", "iresha_nethmini.jpg"),
    Person("Dhananji Thakshila", 3, "Research Team Member",
           "Department of Computer Science", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "it22223012@my.sliit.lk", "dhananji_thakshila.jpg"),
    Person("Imashi Hasinika", 4, "Research Team Member",
           "Department of Computer Science", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "it20202974@my.sliit.lk", "imashi_hasinika.jpg"),
)

SUPERVISORS = (
    Person("Samadhi Rathnayake", 1, "Supervisor",
           "Department of Computer Science", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "samadhi.r@sliit.lk", "samadhi_rathnayake.jpg"),
    Person("Adya Dissanayake", 2, "Co-Supervisor",
           "Department of Information Technology", INSTITUTION_NAME,
           INSTITUTION_LOCATION, "adya.d@sliit.lk", "adya_dissanayake.jpg"),
)
