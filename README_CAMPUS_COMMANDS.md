# Campus and University Population Commands

This document describes the production-ready commands for populating Tanzanian universities and their campuses in the MwanachuoShop system.

## Commands Overview

### 1. `load_tz_universities` - University Population
Loads comprehensive data for all major Tanzanian universities and institutes.

### 2. `populate_campuses_production` - Campus Population  
Populates detailed campus information for all universities with accurate coordinates and addresses.

## Usage Instructions

### Step 1: Load Universities

First, populate the universities:

```bash
# Run inside Docker container
docker-compose run --rm web python manage.py load_tz_universities

# Options:
# --dry-run: Show what would be created without creating records
# --update-existing: Update existing universities with new data

# Examples:
docker-compose run --rm web python manage.py load_tz_universities --dry-run
docker-compose run --rm web python manage.py load_tz_universities --update-existing
```

### Step 2: Populate Campuses

Then, populate the campuses for all universities:

```bash
# Run inside Docker container
docker-compose run --rm web python manage.py populate_campuses_production

# Options:
# --dry-run: Show what would be created without creating records
# --university "University Name": Create campuses for a specific university only

# Examples:
docker-compose run --rm web python manage.py populate_campuses_production --dry-run
docker-compose run --rm web python manage.py populate_campuses_production --university "University of Dar es Salaam"
```

## Data Coverage

### Universities Included (60+ institutions)

**Major Public Universities:**
- University of Dar es Salaam (UDSM)
- Ardhi University (ARU)
- Muhimbili University of Health and Allied Sciences (MUHAS)
- Sokoine University of Agriculture (SUA)
- University of Dodoma (UDOM)
- Nelson Mandela African Institution of Science and Technology (NM-AIST)
- Mbeya University of Science and Technology (MUST)

**Private Universities:**
- St. Augustine University of Tanzania (SAUT)
- Tumaini University Makumira (TUMA)
- Open University of Tanzania (OUT)
- Dar es Salaam Institute of Technology (DIT)
- Institute of Finance Management (IFM)
- Institute of Accountancy Arusha (IAA)
- Zanzibar University (ZU)
- And many more...

**Regional Universities:**
- University of Kigoma, Singida, Tabora, Shinyanga, Mara, Manyara, Ruvuma, Lindi, Coast Region, Kagera, Geita, Simiyu, Katavi, Njombe, Songwe
- Zanzibar regional universities (Kaskazini Pemba, Kusini Pemba, Kusini Unguja, Kaskazini Unguja, Mjini Magharibi)

### Campus Data Included

Each university includes:
- **Main Campus** with accurate coordinates
- **Extension Campuses** where applicable
- **Detailed addresses** and descriptions
- **Geographic coordinates** (latitude/longitude)
- **Campus descriptions** for context

## Example Campus Data

### University of Dar es Salaam
- Mlimani Campus (Main campus with most faculties)
- Muhimbili Campus (Health sciences campus)
- Dar es Salaam University College of Education (DUCE)
- Mkwawa University College of Education (MUCE)

### Ardhi University
- Main Campus (Built environment studies)
- Mbezi Beach Campus (Extension campus)

### Muhimbili University of Health and Allied Sciences
- Muhimbili Campus (Main health sciences campus)
- Mloganzila Campus (New teaching hospital campus)

## Production Features

### Error Handling
- Comprehensive error handling and logging
- Graceful handling of missing universities
- Detailed error reporting

### Data Validation
- Coordinate validation
- Address verification
- Duplicate prevention

### Performance
- Efficient database operations
- Bulk operations where possible
- Progress reporting

### Safety Features
- Dry-run mode for testing
- Selective university processing
- Update existing records option

## Database Schema

### University Model
```python
class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
```

### Campus Model
```python
class Campus(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

## Verification Commands

After running the population commands, verify the data:

```bash
# Check total counts
docker-compose run --rm web python manage.py shell -c "
from core.models import University, Campus
print(f'Universities: {University.objects.count()}')
print(f'Campuses: {Campus.objects.count()}')
print(f'Active Universities: {University.objects.filter(is_active=True).count()}')
print(f'Active Campuses: {Campus.objects.filter(is_active=True).count()}')
"

# Check specific university
docker-compose run --rm web python manage.py shell -c "
from core.models import University, Campus
uni = University.objects.get(name='University of Dar es Salaam')
print(f'University: {uni.name}')
print(f'Campuses: {uni.campuses.count()}')
for campus in uni.campuses.all():
    print(f'  - {campus.name}: {campus.address}')
"
```

## Troubleshooting

### Common Issues

1. **University not found errors**
   - Ensure universities are loaded first
   - Check university name spelling in campus data

2. **Coordinate errors**
   - Verify latitude/longitude format
   - Check for valid decimal values

3. **Database connection issues**
   - Ensure Docker containers are running
   - Check database connectivity

### Debug Commands

```bash
# Check existing universities
docker-compose run --rm web python manage.py shell -c "
from core.models import University
for uni in University.objects.all()[:10]:
    print(f'{uni.name} ({uni.short_name})')
"

# Check existing campuses
docker-compose run --rm web python manage.py shell -c "
from core.models import Campus
for campus in Campus.objects.all()[:10]:
    print(f'{campus.name} - {campus.university.name}')
"
```

## Maintenance

### Updating Data
To update existing data with new information:

```bash
# Update universities
docker-compose run --rm web python manage.py load_tz_universities --update-existing

# Update campuses (will update existing and create new)
docker-compose run --rm web python manage.py populate_campuses_production
```

### Adding New Universities
1. Add university data to `UNIVERSITIES` list in `load_tz_universities.py`
2. Add campus data to `CAMPUS_DATA` in `populate_campuses_production.py`
3. Run the commands

### Data Sources
- Official university websites
- Government education databases
- Geographic coordinate databases
- Local knowledge and verification

## Support

For issues or questions about these commands:
1. Check the error logs
2. Verify database connectivity
3. Test with dry-run mode first
4. Contact the development team 