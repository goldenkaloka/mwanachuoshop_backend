from django.core.management.base import BaseCommand
from core.models import University
from django.contrib.gis.geos import Point

# Comprehensive list of Tanzanian universities and major institutes (2024-2025)
UNIVERSITIES = [
    # Major Public Universities
    {"name": "University of Dar es Salaam", "short_name": "UDSM", "city": "Dar es Salaam", "latitude": -6.7735, "longitude": 39.2692},
    {"name": "Ardhi University", "short_name": "ARU", "city": "Dar es Salaam", "latitude": -6.7750, "longitude": 39.1270},
    {"name": "Muhimbili University of Health and Allied Sciences", "short_name": "MUHAS", "city": "Dar es Salaam", "latitude": -6.8147, "longitude": 39.2796},
    {"name": "Sokoine University of Agriculture", "short_name": "SUA", "city": "Morogoro", "latitude": -6.8278, "longitude": 37.6612},
    {"name": "University of Dodoma", "short_name": "UDOM", "city": "Dodoma", "latitude": -6.1778, "longitude": 35.7497},
    {"name": "Nelson Mandela African Institution of Science and Technology", "short_name": "NM-AIST", "city": "Arusha", "latitude": -3.3869, "longitude": 36.8156},
    {"name": "Mbeya University of Science and Technology", "short_name": "MUST", "city": "Mbeya", "latitude": -8.9117, "longitude": 33.4586},
    
    # Private Universities
    {"name": "St. Augustine University of Tanzania", "short_name": "SAUT", "city": "Mwanza", "latitude": -2.5164, "longitude": 32.9000},
    {"name": "Tumaini University Makumira", "short_name": "TUMA", "city": "Arusha", "latitude": -3.3750, "longitude": 36.7847},
    {"name": "Open University of Tanzania", "short_name": "OUT", "city": "Dar es Salaam", "latitude": -6.8190, "longitude": 39.2886},
    {"name": "Dar es Salaam Institute of Technology", "short_name": "DIT", "city": "Dar es Salaam", "latitude": -6.8176, "longitude": 39.2882},
    {"name": "Institute of Finance Management", "short_name": "IFM", "city": "Dar es Salaam", "latitude": -6.8132, "longitude": 39.2886},
    {"name": "Institute of Accountancy Arusha", "short_name": "IAA", "city": "Arusha", "latitude": -3.3869, "longitude": 36.6829},
    {"name": "Zanzibar University", "short_name": "ZU", "city": "Zanzibar", "latitude": -6.2000, "longitude": 39.2500},
    {"name": "Hubert Kairuki Memorial University", "short_name": "HKMU", "city": "Dar es Salaam", "latitude": -6.7992, "longitude": 39.2742},
    {"name": "Ruaha Catholic University", "short_name": "RUCU", "city": "Iringa", "latitude": -7.7700, "longitude": 35.6900},
    {"name": "Mzumbe University", "short_name": "MU", "city": "Morogoro", "latitude": -6.8361, "longitude": 37.6622},
    {"name": "Catholic University of Health and Allied Sciences", "short_name": "CUHAS", "city": "Mwanza", "latitude": -2.5164, "longitude": 32.9000},
    {"name": "Teofilo Kisanji University", "short_name": "TEKU", "city": "Mbeya", "latitude": -8.9090, "longitude": 33.4600},
    {"name": "St. John's University of Tanzania", "short_name": "SJUT", "city": "Dodoma", "latitude": -6.1630, "longitude": 35.7516},
    {"name": "State University of Zanzibar", "short_name": "SUZA", "city": "Zanzibar", "latitude": -6.1659, "longitude": 39.2026},
    {"name": "Mount Meru University", "short_name": "MMU", "city": "Arusha", "latitude": -3.3869, "longitude": 36.6829},
    {"name": "University of Iringa", "short_name": "UOI", "city": "Iringa", "latitude": -7.7700, "longitude": 35.6900},
    {"name": "University of Bagamoyo", "short_name": "UB", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Muslim University of Morogoro", "short_name": "MUM", "city": "Morogoro", "latitude": -6.8278, "longitude": 37.6612},
    {"name": "University of Arusha", "short_name": "UOA", "city": "Arusha", "latitude": -3.3869, "longitude": 36.6829},
    {"name": "St. Joseph University in Tanzania", "short_name": "SJUIT", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Eckernforde Tanga University", "short_name": "ETU", "city": "Tanga", "latitude": -5.0689, "longitude": 39.0988},
    {"name": "United African University of Tanzania", "short_name": "UAUT", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Sebastian Kolowa Memorial University", "short_name": "SEKOMU", "city": "Lushoto", "latitude": -4.7650, "longitude": 38.2875},
    {"name": "Moshi Co-operative University", "short_name": "MoCU", "city": "Moshi", "latitude": -3.3349, "longitude": 37.3400},
    {"name": "Katavi University of Agriculture", "short_name": "KUA", "city": "Mpanda", "latitude": -6.3431, "longitude": 31.0672},
    {"name": "Mbeya University College of Health and Allied Sciences", "short_name": "MUCHAS", "city": "Mbeya", "latitude": -8.9117, "longitude": 33.4586},
    {"name": "Dar es Salaam University College of Education", "short_name": "DUCE", "city": "Dar es Salaam", "latitude": -6.8190, "longitude": 39.2886},
    {"name": "Mkwawa University College of Education", "short_name": "MUCE", "city": "Iringa", "latitude": -7.7700, "longitude": 35.6900},
    {"name": "Stefano Moshi Memorial University College", "short_name": "SMMUCO", "city": "Moshi", "latitude": -3.3349, "longitude": 37.3400},
    {"name": "Stella Maris Mtwara University College", "short_name": "STEMMUCO", "city": "Mtwara", "latitude": -10.2667, "longitude": 40.1833},
    {"name": "Kampala International University Dar es Salaam College", "short_name": "KIU-DAR", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Kilimanjaro Christian Medical University College", "short_name": "KCMUCo", "city": "Moshi", "latitude": -3.3349, "longitude": 37.3400},
    {"name": "St. Francis University College of Health and Allied Sciences", "short_name": "SFUCHAS", "city": "Morogoro", "latitude": -6.8278, "longitude": 37.6612},
    {"name": "Tumaini University Dar es Salaam College", "short_name": "TUDARCo", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Mwenge Catholic University", "short_name": "MWUCE", "city": "Moshi", "latitude": -3.3349, "longitude": 37.3400},
    {"name": "St. Joseph University College of Agricultural Sciences and Technology", "short_name": "SJUCAST", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "St. Joseph University College of Information and Technology", "short_name": "SJUCIT", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "St. Joseph University College of Management and Commerce", "short_name": "SJUCMC", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Canada Education Support Network", "short_name": "CESUNE COLLEGE", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "Al-Maktoum College of Engineering and Technology", "short_name": "AMCET", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    
    # Additional Universities and Colleges
    {"name": "University of Kigoma", "short_name": "UOK", "city": "Kigoma", "latitude": -4.8769, "longitude": 29.6267},
    {"name": "University of Singida", "short_name": "UOS", "city": "Singida", "latitude": -4.8167, "longitude": 34.7500},
    {"name": "University of Tabora", "short_name": "UOT", "city": "Tabora", "latitude": -5.0167, "longitude": 32.8000},
    {"name": "University of Shinyanga", "short_name": "UOSH", "city": "Shinyanga", "latitude": -3.6667, "longitude": 33.4333},
    {"name": "University of Mara", "short_name": "UOM", "city": "Musoma", "latitude": -1.5000, "longitude": 33.8000},
    {"name": "University of Manyara", "short_name": "UOMY", "city": "Babati", "latitude": -4.2167, "longitude": 35.7500},
    {"name": "University of Ruvuma", "short_name": "UOR", "city": "Songea", "latitude": -10.6833, "longitude": 35.6500},
    {"name": "University of Lindi", "short_name": "UOL", "city": "Lindi", "latitude": -9.9833, "longitude": 39.7167},
    {"name": "University of Coast Region", "short_name": "UOCR", "city": "Dar es Salaam", "latitude": -6.8235, "longitude": 39.2695},
    {"name": "University of Kagera", "short_name": "UOKG", "city": "Bukoba", "latitude": -1.3333, "longitude": 31.8167},
    {"name": "University of Geita", "short_name": "UOG", "city": "Geita", "latitude": -2.8667, "longitude": 32.2333},
    {"name": "University of Simiyu", "short_name": "UOSM", "city": "Bariadi", "latitude": -2.8000, "longitude": 33.9833},
    {"name": "University of Katavi", "short_name": "UOKT", "city": "Mpanda", "latitude": -6.3431, "longitude": 31.0672},
    {"name": "University of Njombe", "short_name": "UONJ", "city": "Njombe", "latitude": -9.3333, "longitude": 34.7667},
    {"name": "University of Songwe", "short_name": "UOSG", "city": "Vwawa", "latitude": -9.2000, "longitude": 32.9333},
    {"name": "University of Kaskazini Pemba", "short_name": "UOKP", "city": "Wete", "latitude": -5.0667, "longitude": 39.7167},
    {"name": "University of Kusini Pemba", "short_name": "UOKSP", "city": "Chake Chake", "latitude": -5.2500, "longitude": 39.7667},
    {"name": "University of Kusini Unguja", "short_name": "UOKU", "city": "Koani", "latitude": -6.1333, "longitude": 39.2833},
    {"name": "University of Kaskazini Unguja", "short_name": "UOKKU", "city": "Mkokotoni", "latitude": -5.8833, "longitude": 39.2667},
    {"name": "University of Mjini Magharibi", "short_name": "UOMM", "city": "Zanzibar", "latitude": -6.1659, "longitude": 39.2026},
]

class Command(BaseCommand):
    help = "Load all known universities and institutes in Tanzania into the University model."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing universities with new data',
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get('dry_run', False)
        update_existing = kwargs.get('update_existing', False)
        
        created = 0
        updated = 0
        skipped = 0
        
        self.stdout.write(self.style.SUCCESS("Starting university population..."))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No records will be created"))
        
        for uni in UNIVERSITIES:
            try:
                # Check if university already exists
                existing_uni = University.objects.filter(name=uni["name"]).first()
                
                if existing_uni:
                    if update_existing and not dry_run:
                        # Update existing university
                        existing_uni.short_name = uni["short_name"]
                        existing_uni.location = Point(float(uni["longitude"]), float(uni["latitude"]))
                        existing_uni.radius_km = 5.00
                        existing_uni.is_active = True
                        existing_uni.save()
                        updated += 1
                        self.stdout.write(f"Updated: {existing_uni.name}")
                    else:
                        skipped += 1
                        if dry_run:
                            self.stdout.write(f"Would skip (exists): {uni['name']}")
                        else:
                            self.stdout.write(f"Skipped (exists): {uni['name']}")
                else:
                    if not dry_run:
                        # Create new university
                        obj = University.objects.create(
                name=uni["name"],
                            short_name=uni["short_name"],
                            location=Point(float(uni["longitude"]), float(uni["latitude"])),
                            radius_km=5.00,
                            is_active=True,
                        )
                created += 1
                        self.stdout.write(f"Created: {obj.name}")
                    else:
                        self.stdout.write(f"Would create: {uni['name']}")
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing {uni['name']}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("UNIVERSITY POPULATION SUMMARY"))
        self.stdout.write("="*50)
        
        if dry_run:
            self.stdout.write(f"Would create: {created} universities")
            self.stdout.write(f"Would update: {updated} universities")
            self.stdout.write(f"Would skip: {skipped} universities")
            else:
            self.stdout.write(f"Created: {created} universities")
            self.stdout.write(f"Updated: {updated} universities")
            self.stdout.write(f"Skipped: {skipped} universities")
        
        self.stdout.write(f"Total universities in database: {University.objects.count()}")
        self.stdout.write(self.style.SUCCESS("University population completed!")) 