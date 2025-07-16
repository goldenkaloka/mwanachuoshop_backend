 from django.core.management.base import BaseCommand
from core.models import University, Campus
from decimal import Decimal
import logging
from django.contrib.gis.geos import Point

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate comprehensive campus data for all major Tanzanian universities (Production Ready)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--university',
            type=str,
            help='Create campuses for a specific university only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_university = options['university']
        
        # Comprehensive campus data for Tanzanian universities
        CAMPUS_DATA = {
            "University of Dar es Salaam": {
                "campuses": [
                    {
                        "name": "Mlimani Campus",
                        "address": "Mlimani Road, Dar es Salaam",
                        "latitude": -6.7735,
                        "longitude": 39.2692
                    },
                    {
                        "name": "Muhimbili Campus",
                        "address": "Muhimbili, Dar es Salaam",
                        "latitude": -6.8124,
                        "longitude": 39.2331
                    },
                    {
                        "name": "Dar es Salaam University College of Education (DUCE)",
                        "address": "Chang'ombe, Dar es Salaam",
                        "latitude": -6.8190,
                        "longitude": 39.2886
                    },
                    {
                        "name": "Mkwawa University College of Education (MUCE)",
                        "address": "Iringa, Tanzania",
                        "latitude": -7.7700,
                        "longitude": 35.6900
                    }
                ]
            },
            "Ardhi University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mlimani, Dar es Salaam",
                        "latitude": -6.7750,
                        "longitude": 39.1270
                    },
                    {
                        "name": "Mbezi Beach Campus",
                        "address": "Mbezi Beach, Dar es Salaam",
                        "latitude": -6.7500,
                        "longitude": 39.2000
                    }
                ]
            },
            "Muhimbili University of Health and Allied Sciences": {
                "campuses": [
                    {
                        "name": "Muhimbili Campus",
                        "address": "Muhimbili, Dar es Salaam",
                        "latitude": -6.8147,
                        "longitude": 39.2796
                    },
                    {
                        "name": "Mloganzila Campus",
                        "address": "Mloganzila, Dar es Salaam",
                        "latitude": -6.8500,
                        "longitude": 39.2000
                    }
                ]
            },
            "Sokoine University of Agriculture": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Sokoine, Morogoro",
                        "latitude": -6.8278,
                        "longitude": 37.6612
                    },
                    {
                        "name": "Solomon Mahlangu Campus",
                        "address": "Morogoro, Tanzania",
                        "latitude": -6.8300,
                        "longitude": 37.6600
                    }
                ]
            },
            "University of Dodoma": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dodoma, Tanzania",
                        "latitude": -6.1778,
                        "longitude": 35.7497
                    },
                    {
                        "name": "College of Business and Law",
                        "address": "Dodoma, Tanzania",
                        "latitude": -6.1780,
                        "longitude": 35.7500
                    }
                ]
            },
            "Nelson Mandela African Institution of Science and Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Arusha, Tanzania",
                        "latitude": -3.3869,
                        "longitude": 36.8156
                    }
                ]
            },
            "Mbeya University of Science and Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mbeya, Tanzania",
                        "latitude": -8.9117,
                        "longitude": 33.4586
                    }
                ]
            },
            "St. Augustine University of Tanzania": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mwanza, Tanzania",
                        "latitude": -2.5164,
                        "longitude": 32.9000
                    },
                    {
                        "name": "Dar es Salaam Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Tumaini University Makumira": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Makumira, Arusha",
                        "latitude": -3.3750,
                        "longitude": 36.7847
                    },
                    {
                        "name": "Dar es Salaam Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Open University of Tanzania": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Kinondoni, Dar es Salaam",
                        "latitude": -6.8190,
                        "longitude": 39.2886
                    },
                    {
                        "name": "Regional Centers",
                        "address": "Various locations across Tanzania",
                        "latitude": -6.8190,
                        "longitude": 39.2886
                    }
                ]
            },
            "Dar es Salaam Institute of Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Ilala, Dar es Salaam",
                        "latitude": -6.8176,
                        "longitude": 39.2882
                    }
                ]
            },
            "Institute of Finance Management": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8132,
                        "longitude": 39.2886
                    },
                    {
                        "name": "Dodoma Campus",
                        "address": "Dodoma, Tanzania",
                        "latitude": -6.1778,
                        "longitude": 35.7497
                    },
                    {
                        "name": "Mwanza Campus",
                        "address": "Mwanza, Tanzania",
                        "latitude": -2.5164,
                        "longitude": 32.9000
                    }
                ]
            },
            "Institute of Accountancy Arusha": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Arusha, Tanzania",
                        "latitude": -3.3869,
                        "longitude": 36.6829
                    },
                    {
                        "name": "Dar es Salaam Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Zanzibar University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Zanzibar, Tanzania",
                        "latitude": -6.2000,
                        "longitude": 39.2500
                    }
                ]
            },
            "Hubert Kairuki Memorial University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.7992,
                        "longitude": 39.2742
                    }
                ]
            },
            "Ruaha Catholic University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Iringa, Tanzania",
                        "latitude": -7.7700,
                        "longitude": 35.6900
                    }
                ]
            },
            "Mzumbe University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mzumbe, Morogoro",
                        "latitude": -6.8361,
                        "longitude": 37.6622
                    },
                    {
                        "name": "Dar es Salaam Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Catholic University of Health and Allied Sciences": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mwanza, Tanzania",
                        "latitude": -2.5164,
                        "longitude": 32.9000
                    }
                ]
            },
            "St. John's University of Tanzania": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dodoma, Tanzania",
                        "latitude": -6.1630,
                        "longitude": 35.7516
                    }
                ]
            },
            "State University of Zanzibar": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Zanzibar, Tanzania",
                        "latitude": -6.1659,
                        "longitude": 39.2026
                    }
                ]
            },
            "Mount Meru University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Arusha, Tanzania",
                        "latitude": -3.3869,
                        "longitude": 36.6829
                    }
                ]
            },
            "University of Iringa": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Iringa, Tanzania",
                        "latitude": -7.7700,
                        "longitude": 35.6900
                    }
                ]
            },
            "University of Bagamoyo": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Bagamoyo, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Muslim University of Morogoro": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Morogoro, Tanzania",
                        "latitude": -6.8278,
                        "longitude": 37.6612
                    }
                ]
            },
            "University of Arusha": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Arusha, Tanzania",
                        "latitude": -3.3869,
                        "longitude": 36.6829
                    }
                ]
            },
            "St. Joseph University in Tanzania": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Eckernforde Tanga University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Tanga, Tanzania",
                        "latitude": -5.0689,
                        "longitude": 39.0988
                    }
                ]
            },
            "United African University of Tanzania": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Sebastian Kolowa Memorial University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Lushoto, Tanzania",
                        "latitude": -4.7650,
                        "longitude": 38.2875
                    }
                ]
            },
            "Moshi Co-operative University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Moshi, Tanzania",
                        "latitude": -3.3349,
                        "longitude": 37.3400
                    }
                ]
            },
            "Katavi University of Agriculture": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mpanda, Tanzania",
                        "latitude": -6.3431,
                        "longitude": 31.0672
                    }
                ]
            },
            "Mbeya University College of Health and Allied Sciences": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mbeya, Tanzania",
                        "latitude": -8.9117,
                        "longitude": 33.4586
                    }
                ]
            },
            "Dar es Salaam University College of Education": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Chang'ombe, Dar es Salaam",
                        "latitude": -6.8190,
                        "longitude": 39.2886
                    }
                ]
            },
            "Mkwawa University College of Education": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Iringa, Tanzania",
                        "latitude": -7.7700,
                        "longitude": 35.6900
                    }
                ]
            },
            "Stefano Moshi Memorial University College": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Moshi, Tanzania",
                        "latitude": -3.3349,
                        "longitude": 37.3400
                    }
                ]
            },
            "Stella Maris Mtwara University College": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Mtwara, Tanzania",
                        "latitude": -10.2667,
                        "longitude": 40.1833
                    }
                ]
            },
            "Kampala International University Dar es Salaam College": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Kilimanjaro Christian Medical University College": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Moshi, Tanzania",
                        "latitude": -3.3349,
                        "longitude": 37.3400
                    }
                ]
            },
            "St. Francis University College of Health and Allied Sciences": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Morogoro, Tanzania",
                        "latitude": -6.8278,
                        "longitude": 37.6612
                    }
                ]
            },
            "Tumaini University Dar es Salaam College": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Mwenge Catholic University": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Moshi, Tanzania",
                        "latitude": -3.3349,
                        "longitude": 37.3400
                    }
                ]
            },
            "St. Joseph University College of Agricultural Sciences and Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "St. Joseph University College of Information and Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "St. Joseph University College of Management and Commerce": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Canada Education Support Network": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            },
            "Al-Maktoum College of Engineering and Technology": {
                "campuses": [
                    {
                        "name": "Main Campus",
                        "address": "Dar es Salaam, Tanzania",
                        "latitude": -6.8235,
                        "longitude": 39.2695
                    }
                ]
            }
        }

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(self.style.SUCCESS("Starting comprehensive campus population..."))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No records will be created"))

        # Filter universities if specific university is provided
        if specific_university:
            if specific_university not in CAMPUS_DATA:
                self.stdout.write(
                    self.style.ERROR(f"University '{specific_university}' not found in campus data")
                )
                return
            universities_to_process = {specific_university: CAMPUS_DATA[specific_university]}
        else:
            universities_to_process = CAMPUS_DATA

        for university_name, university_data in universities_to_process.items():
            try:
                # Find the university in the database
                university = University.objects.filter(
                    name__icontains=university_name
                ).first()
                
                if not university:
                    self.stdout.write(
                        self.style.WARNING(f"University '{university_name}' not found in database")
                    )
                    skipped_count += 1
                    continue

                self.stdout.write(f"Processing university: {university.name}")
                
                for campus_info in university_data['campuses']:
                    try:
                        # Check if campus already exists
                        existing_campus = Campus.objects.filter(
                            name=campus_info['name'],
                            university=university
                        ).first()
                        
                        if existing_campus:
                            if not dry_run:
                                # Update existing campus with new information
                                existing_campus.address = campus_info['address']
                                existing_campus.location = Point(float(campus_info['longitude']), float(campus_info['latitude']))
                                existing_campus.is_active = True
                                existing_campus.save()
                                updated_count += 1
                                self.stdout.write(f"  Updated campus: {existing_campus.name}")
                            else:
                                self.stdout.write(f"  Would update campus: {campus_info['name']}")
                            continue
                        
                        if not dry_run:
                            # Create new campus
                            campus = Campus.objects.create(
                                name=campus_info['name'],
                                university=university,
                                address=campus_info['address'],
                                location=Point(float(campus_info['longitude']), float(campus_info['latitude'])),
                                is_active=True
                            )
                            created_count += 1
                            self.stdout.write(f"  Created campus: {campus.name}")
                        else:
                            self.stdout.write(f"  Would create campus: {campus_info['name']}")
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"Error processing campus '{campus_info['name']}': {str(e)}")
                        )
                        logger.error(f"Error creating campus {campus_info['name']}: {str(e)}")
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Error processing university '{university_name}': {str(e)}")
                )
                logger.error(f"Error processing university {university_name}: {str(e)}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("CAMPUS POPULATION SUMMARY"))
        self.stdout.write("="*50)
        
        if dry_run:
            self.stdout.write(f"Would create: {created_count} campuses")
            self.stdout.write(f"Would update: {updated_count} campuses")
        else:
            self.stdout.write(f"Created: {created_count} campuses")
            self.stdout.write(f"Updated: {updated_count} campuses")
        
        self.stdout.write(f"Skipped: {skipped_count} universities (not found)")
        self.stdout.write(f"Errors: {error_count}")
        self.stdout.write(f"Total campuses in database: {Campus.objects.count()}")
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING("Some errors occurred. Check the logs for details.")
            )
        
        self.stdout.write(self.style.SUCCESS("Campus population completed!")) 