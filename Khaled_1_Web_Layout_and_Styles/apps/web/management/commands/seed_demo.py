"""Demo data for development and the lab demo. Idempotent: safe to run twice.

    python manage.py seed_demo
Every demo user's password is "demo-pass-2026". The structure and figures are illustrations, not KU's real
rules or inventory.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.access.models import PERMISSIONS, Department, Permission, Role, RoleAssignment, User
from apps.ai.models import AICapability, ModelVersion
from apps.sustainability.models import EmissionFactor
from apps.catalogue.models import Asset, AssetTag, Category
from apps.common.enums import Condition

PASSWORD = "demo-pass-2026"

ROLES_AR = {"Requester": "مقدّم طلب", "Asset Custodian": "أمين الأصول", "Approver": "معتمِد", "Facilities": "المرافق",
            "Maintenance Staff": "فريق الصيانة", "Sustainability Officer": "مسؤول الاستدامة", "System Administrator": "مسؤول النظام"}
CATEGORIES_AR = {"IT Equipment": "معدات تقنية المعلومات", "Monitors": "شاشات", "Docking stations": "محطات توصيل", "Projectors": "أجهزة عرض",
                 "Furniture": "أثاث", "Chairs": "كراسي", "Stools": "مقاعد", "Shelving": "رفوف", "Whiteboards": "سبورات",
                 "Lab Equipment": "معدات المختبرات", "Oscilloscopes": "راسمات الذبذبات", "Power supplies": "مزودات الطاقة", "3D printers": "طابعات ثلاثية الأبعاد"}

ROLES = {
    # name: (permission codes, approval limit AED or None)
    "Requester": (["request.submit", "transfer.receive"], None),
    "Asset Custodian": (["asset.register", "asset.publish", "asset.custody", "maintenance.record", "eol.propose"], None),
    "Approver": (["request.approve", "eol.approve", "reports.view"], Decimal("2000")),
    "Facilities": (["transfer.dispatch"], None),
    "Maintenance Staff": (["maintenance.record"], None),
    "Sustainability Officer": (["sustainability.review", "reports.view", "reports.publish"], None),
    "System Administrator": (["admin.users", "admin.blueprint", "admin.ai", "reports.view"], None),
}

CATEGORIES = [  # (name, parent, icon, material)
    ("IT Equipment", None, "laptop", "Electronics"), ("Monitors", "IT Equipment", "monitor", "Electronics"),
    ("Docking stations", "IT Equipment", "dock", "Electronics"), ("Projectors", "IT Equipment", "projector", "Electronics"),
    ("Furniture", None, "chair", "Mixed"), ("Chairs", "Furniture", "chair", "Steel and fabric"),
    ("Stools", "Furniture", "stool", "Steel and plastic"), ("Whiteboards", "Furniture", "board", "Steel and laminate"),
    ("Shelving", "Furniture", "shelf", "Wood"),
    ("Lab Equipment", None, "scope", "Electronics"), ("Oscilloscopes", "Lab Equipment", "scope", "Electronics"),
    ("Power supplies", "Lab Equipment", "power", "Electronics"), ("3D printers", "Lab Equipment", "printer", "Electronics"),
]

ASSETS = [  # name, category, unit, campus, building, room, condition, qty, value, purchased, specs, tags, publish
    ("Dell 24-inch monitor", "Monitors", "Computer Science", "Main", "B1", "1.12", Condition.GOOD, 6, "650", date(2022, 9, 1), "24 in, 1920×1080, HDMI and DisplayPort", "monitor, 24-inch, HDMI", True),
    ("Samsung 27-inch monitor", "Monitors", "Mechanical Engineering", "Main", "B2", "0.04", Condition.GOOD, 2, "900", date(2023, 2, 1), "27 in, 2560×1440, USB-C", "monitor, 27-inch, USB-C", True),
    ("LG 22-inch monitor", "Monitors", "Library", "SAN", "Library", "Level 1", Condition.FAIR, 6, "450", date(2019, 8, 1), "22 in, 1920×1080, HDMI and VGA", "monitor, 22-inch, VGA", True),
    ("Ergonomic office chair", "Chairs", "Mechanical Engineering", "Main", "B2", "2.10", Condition.FAIR, 10, "400", date(2020, 1, 15), "Adjustable height, armrests", "chair, adjustable, armrests", True),
    ("Stackable lab stool", "Stools", "Chemistry", "Main", "B4", "Teaching lab 3", Condition.GOOD, 12, "180", date(2021, 9, 1), "Chemical-resistant seat, stackable", "stool, lab, stackable", True),
    ("Digital oscilloscope, 100 MHz", "Oscilloscopes", "Electrical Engineering", "Masdar", "M1", "0.21", Condition.GOOD, 1, "1800", date(2021, 3, 1), "100 MHz, 2 channels, USB export", "oscilloscope, 2-channel", True),
    ("Desktop 3D printer", "3D printers", "Makerspace", "Main", "Library", "Makerspace", Condition.FAIR, 1, "2800", date(2020, 10, 1), "250 × 210 × 210 mm build, PLA and PETG", "3d printer, PLA", True),
    ("Mobile whiteboard", "Whiteboards", "College of Engineering", "Main", "B1", "Corridor store", Condition.GOOD, 3, "750", date(2022, 1, 10), "180 × 90 cm, double-sided, on wheels", "whiteboard, wheels, double-sided", True),
    ("Bench power supply, 30 V", "Power supplies", "Electrical Engineering", "Masdar", "M1", "0.18", Condition.GOOD, 3, "900", date(2022, 5, 1), "0–30 V, 0–3 A, dual output", "power supply, 30V, 3A", True),
    ("Laptop docking station", "Docking stations", "Computer Science", "Main", "B1", "1.05", Condition.NEW, 8, "520", date(2025, 8, 20), "USB-C, two display outputs, 90 W", "dock, USB-C, dual display", True),
    ("Classroom projector", "Projectors", "Library", "SAN", "Library", "AV store", Condition.GOOD, 2, "2100", date(2021, 6, 1), "4,000 lumens, HDMI, ceiling bracket included", "projector, 4000 lumens, HDMI", True),
    ("Bookshelf, five shelves", "Shelving", "Library", "SAN", "Library", "Store B", Condition.GOOD, 5, "350", date(2018, 2, 1), "180 × 80 cm, laminated wood", "bookshelf, wood", True),
    ("Wooden lectern", "Furniture", "Computer Science", "Main", "B1", "3.01", Condition.GOOD, 1, "600", date(2017, 9, 1), "Adjustable top, cable port", "lectern, podium", False),
]


class Command(BaseCommand):
    help = "Create demo units, roles, users, categories, assets and AI model versions."

    @transaction.atomic
    def handle(self, *args, **opts):
        for code, desc in PERMISSIONS.items():
            Permission.objects.update_or_create(code=code, defaults={"description": desc})
        roles = {}
        for name, (codes, limit) in ROLES.items():
            role, _ = Role.objects.update_or_create(name=name, defaults={"approval_limit": limit, "name_ar": ROLES_AR.get(name, "")})
            role.permissions.set(codes)
            roles[name] = role

        def unit(name, parent=None, unit_type="Department", campus="Main", building=""):
            d, _ = Department.objects.get_or_create(name=name, defaults={"parent": parent, "unit_type": unit_type, "campus": campus, "building": building})
            return d

        uni = unit("Demo University", unit_type="University")
        eng = unit("College of Engineering", uni, "College", building="B1")
        sci = unit("College of Science", uni, "College", building="B4")
        cs, me, ee = unit("Computer Science", eng, building="B1"), unit("Mechanical Engineering", eng, building="B2"), unit("Electrical Engineering", eng, campus="Masdar", building="M1")
        chem = unit("Chemistry", sci, building="B4")
        lib = unit("Library", uni, "Service", campus="SAN")
        maker = unit("Makerspace", lib, "Lab", building="Library")
        clubs = unit("Student Clubs", uni, "Office", building="Student Centre")
        units = {d.name: d for d in Department.objects.all()}

        def person(email, name, dept, *assignments):
            u = User.objects.filter(email=email).first()
            if u is None:
                u = User.objects.create_user(email, PASSWORD, full_name=name, department=dept)
            for role_name, scope in assignments:
                RoleAssignment.objects.get_or_create(user=u, role=roles[role_name], scope_department=scope)
            return u

        cara = person("custodian@demo.local", "Cara Custodian", cs, ("Asset Custodian", eng))
        lina = person("lina@demo.local", "Lina Haddad", lib, ("Asset Custodian", lib), ("Asset Custodian", sci))
        person("approver@demo.local", "Adam Approver", eng, ("Approver", eng))
        person("dean@demo.local", "Dana Dean", uni, ("Approver", None))
        person("requester@demo.local", "Rana Requester", me, ("Requester", me))
        person("club@demo.local", "Omar Club President", clubs, ("Requester", clubs))
        person("facilities@demo.local", "Faisal Facilities", uni, ("Facilities", None))
        person("tech@demo.local", "Tariq Technician", uni, ("Maintenance Staff", None))
        person("sustain@demo.local", "Sara Sustainability", uni, ("Sustainability Officer", None))
        person("admin@demo.local", "Ali Admin", uni, ("System Administrator", None))
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("dev@demo.local", PASSWORD)

        cats = {}
        for name, parent, icon, material in CATEGORIES:
            c, _ = Category.objects.get_or_create(name=name, parent=cats.get(parent), defaults={"icon": icon, "material_type": material})
            if c.icon != icon or c.name_ar != CATEGORIES_AR.get(name, c.name_ar):
                c.icon, c.name_ar = icon, CATEGORIES_AR.get(name, c.name_ar)
                c.save(update_fields=["icon", "name_ar"])
            cats[name] = c

        for (name, cat, owner, campus, building, room, cond, qty, value, bought, specs, tags, publish) in ASSETS:
            if Asset.objects.filter(name=name).exists():
                continue
            dept = units[owner]
            custodian = lina if dept.is_within(lib) or dept.is_within(sci) else cara
            a = Asset.objects.create(name=name, category=cats[cat], owner_department=dept, custodian=custodian, quantity=qty,
                                     available_quantity=qty, condition=cond, estimated_value=Decimal(value), purchase_date=bought,
                                     specifications=specs, location_campus=campus, location_building=building, location_room=room)
            a._emit("", custodian, "REGISTRATION", f"Registered {qty} unit(s) in {dept}")
            for t in tags.split(","):
                AssetTag.objects.get_or_create(asset=a, tag_text=t.strip())
            if publish:
                a.mark_available(custodian)
                a.publish(custodian)

        # Phase 6: ten office chairs that will be free after the Mechanical Engineering office refit.
        if not Asset.objects.filter(name="Office chair, mesh back").exists():
            ch = Asset.objects.create(name="Office chair, mesh back", category=cats["Chairs"], owner_department=units["Mechanical Engineering"],
                                      custodian=cara, quantity=10, available_quantity=10, condition="GOOD", estimated_value=Decimal("380"),
                                      purchase_date=date(2021, 9, 1), specifications="Mesh back, adjustable height, armrests",
                                      location_campus="Main", location_building="B2", location_room="2.14")
            ch._emit("", cara, "REGISTRATION", "Registered 10 unit(s) in Mechanical Engineering")
            ch.set_expected(date(2027, 1, 1) if date.today() < date(2027, 1, 1) else date.today() + timedelta(days=30),
                            "Free after the office refit", cara)

        # Sample factors so the Impact page has numbers. Clearly labelled: replace with locally selected factors.
        sample = "Sample value for demonstration. Replace with a locally selected factor."
        for cat_name, kg, mass in [("Monitors", "300", "5"), ("Chairs", "70", "15"), ("Stools", "25", "5"),
                                   ("Projectors", "200", "4"), ("Docking stations", "30", "0.5"), ("Shelving", "120", "30"),
                                   ("Oscilloscopes", "180", "6"), ("3D printers", "150", "15")]:
            cat = Category.objects.filter(name=cat_name).first()
            if cat and not EmissionFactor.objects.filter(category=cat).exists():
                EmissionFactor.objects.create(category=cat, kg_co2e_per_unit=Decimal(kg), mass_kg_per_unit=Decimal(mass),
                                              source=sample, source_date=date(2026, 11, 1), boundary="Cradle-to-gate (assumed)")

        for cap, version, threshold in [(AICapability.CLASSIFY, "cls-0.1", "0.70"), (AICapability.SUMMARIZE, "sum-0.1", None), (AICapability.BLUEPRINT, "bp-0.1", None), (AICapability.RECOMMEND, "adv-0.1", None)]:
            if not ModelVersion.objects.filter(capability=cap).exists():
                real = settings.AI_PROVIDER == "anthropic"
                ModelVersion.objects.create(capability=cap, provider=settings.AI_PROVIDER,
                                            model_name=settings.ANTHROPIC_MODEL if real else "fake", version=version,
                                            low_confidence_threshold=Decimal(threshold) if threshold else None).activate()
        _ = (me, ee, chem, maker, clubs)
        self.stdout.write(self.style.SUCCESS(f"Demo data ready. Sign in as approver@demo.local / {PASSWORD}"))
