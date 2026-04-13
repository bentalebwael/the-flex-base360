# Junior Developer Bug Fix Report by Rifat 
This file is to document all the steps, processes I follow and bugs i find, and how I approached to solve them

## Observations (Not necessarily bad ones only)
1. Docker container build: Worked perfectly, no issue faced. 

**Client Portal:**

2. Client Credentials: 
    - Sunset: worked
    - Ocean: worked
3. Client portal: The list of properties in the property dropdown is same for both client, this seems weird :/
**Update:** all property information are same, this might be correct, as I think the properties are the name of building complex or something, and both clients may have properties in same complex
- in that case, the numbers are exactly same, which must be a problem 
4. The profile links (topbar and sidebar) and route are broken, might not be a issue now,

**Backend API:**
5. Backend API: Swagger UI worked without issue.
6. Testing APIs: some failed to execute without admin credential, using the sunset client's credentials for now, could access some but not all apis. 


## Bugs as complaints:

Issue from **Client B (Ocean Rentals)**:
1. Client B complaint privacy leaked (matches with observation 3):
    - one place found: cache.py, which is passing only the property id, not the tanent id, it is possible both clients may have properties with same property id, which the system is considering same revenue calculation  in properties.
    Fixed: still not showing update in dashboard

Issue found during bug fixing by **Junior Developer (me)**:
2. New errors in database connection: Supabase connection string :3
    - settings does not match with database pool :/
    - fixed, still not working
    - new issue: Incompatible pool class (Fixed by Claude's help)
3. Mock data returns same number for both tenants. (Solved with db pool fix)

Issue from **Dinance Team**:
4. Floating point issue noticed by Finance Team: the current calculation is not precise
    - Seed data: 
    - Fixed in dashboard summary with proper rounding to two decimal points

Issue from **Client A (Sunset Properties)**:
5. The reservation's check_in_date is 2024-02-29 23:30:00+00 — that's February 29 at 11:30 PM in UTC. But prop-001 (Beach House Alpha) is in the Europe/Paris timezone, which is UTC+1. So in Paris local time, that same moment is March 1 at 00:30 AM, calculating the sum in February.
 - Fixed: The updated code builds the boundary in Paris time first, then converts to UTC: