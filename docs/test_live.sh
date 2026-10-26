#!/usr/bin/env bash
set -u

echo "=========================================================="
echo "      LIVE FUNCTIONAL VERIFICATION OF REGISTRATION API    "
echo "=========================================================="

echo -e "\n[TEST 1] Add New Course (CLOUD404)..."
curl -s -i -X POST http://localhost:8072/api/courses \
  -H "Content-Type: application/json" \
  -d '{"code":"CLOUD404","title":"Advanced Cloud Architecture","seats":2}'
echo ""

echo -e "\n[TEST 2] Duplicate Course Code Rejection..."
curl -s -i -X POST http://localhost:8072/api/courses \
  -H "Content-Type: application/json" \
  -d '{"code":"CLOUD404","title":"Duplicate Cloud","seats":5}'
echo ""

echo -e "\n[TEST 3] Add New Student (David Miller)..."
curl -s -i -X POST http://localhost:8072/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"David Miller","email":"david@example.com"}'
echo ""

echo -e "\n[TEST 4] Duplicate Student Email Rejection..."
curl -s -i -X POST http://localhost:8072/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"David Copy","email":"david@example.com"}'
echo ""

echo -e "\n[TEST 5] Register David Miller (id=4) in CLOUD404 (id=4)..."
curl -s -i -X POST http://localhost:8072/api/registrations \
  -H "Content-Type: application/json" \
  -d '{"student_id":4,"course_id":4}'
echo ""

echo -e "\n[TEST 6] Duplicate Registration Rejection..."
curl -s -i -X POST http://localhost:8072/api/registrations \
  -H "Content-Type: application/json" \
  -d '{"student_id":4,"course_id":4}'
echo ""

echo -e "\n[TEST 7] Capacity Limit Rejection (SEC303 is full: 1/1)..."
curl -s -i -X POST http://localhost:8072/api/registrations \
  -H "Content-Type: application/json" \
  -d '{"student_id":1,"course_id":3}'
echo ""

echo -e "\n[TEST 8] View Course Roster for CS101 (id=1)..."
curl -s -i http://localhost:8072/api/courses/1/students
echo ""

echo -e "\n[TEST 9] Cancel Registration in SEC303 (id=3) and Free Seat..."
curl -s -i -X DELETE http://localhost:8072/api/registrations/3
echo ""

echo -e "\n[TEST 10] Register Alice into SEC303 now that seat was freed..."
curl -s -i -X POST http://localhost:8072/api/registrations \
  -H "Content-Type: application/json" \
  -d '{"student_id":1,"course_id":3}'
echo ""

echo -e "\n[TEST 11] Invalid input validation (zero seats and invalid email)..."
curl -s -i -X POST http://localhost:8072/api/courses \
  -H "Content-Type: application/json" \
  -d '{"code":"BAD","title":"Bad Seats","seats":0}'
echo ""
curl -s -i -X POST http://localhost:8072/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Bad Email","email":"not-an-email"}'
echo ""

echo -e "\n[TEST 12] Course deletion cascading registrations..."
# Add temp course
TEMP_C_JSON=$(curl -s -X POST http://localhost:8072/api/courses -H "Content-Type: application/json" -d '{"code":"TEMP999","title":"Temporary Course","seats":5}')
echo "Created temp course: $TEMP_C_JSON"
TEMP_C_ID=$(echo $TEMP_C_JSON | grep -o '"id":[0-9]*' | head -n 1 | cut -d: -f2)
# Register Alice in temp course
curl -s -X POST http://localhost:8072/api/registrations -H "Content-Type: application/json" -d "{\"student_id\":1,\"course_id\":$TEMP_C_ID}"
# Delete temp course
curl -s -i -X DELETE http://localhost:8072/api/courses/$TEMP_C_ID
echo ""

echo -e "\n[TEST 13] Student deletion cascading registrations..."
TEMP_S_JSON=$(curl -s -X POST http://localhost:8072/api/students -H "Content-Type: application/json" -d '{"name":"Temporary Student","email":"tempstudent@example.com"}')
echo "Created temp student: $TEMP_S_JSON"
TEMP_S_ID=$(echo $TEMP_S_JSON | grep -o '"id":[0-9]*' | head -n 1 | cut -d: -f2)
echo "Deleting temp student with ID: $TEMP_S_ID"
curl -s -i -X DELETE http://localhost:8072/api/students/$TEMP_S_ID
echo ""

echo -e "\n[TEST 14] Live Database Status Verification via /api/health..."
curl -s -i http://localhost:8072/api/health
echo ""
