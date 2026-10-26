def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"

def test_create_and_list_course(client):
    res = client.post("/api/courses", json={
        "code": "CS101",
        "title": "Introduction to Computer Science",
        "seats": 2
    })
    assert res.status_code == 201
    course_data = res.json()
    assert course_data["code"] == "CS101"
    assert course_data["seats"] == 2
    assert course_data["enrolled_count"] == 0
    assert course_data["available_seats"] == 2

    # Verify listing
    res_list = client.get("/api/courses")
    assert res_list.status_code == 200
    courses = res_list.json()
    assert any(c["code"] == "CS101" for c in courses)

def test_duplicate_course_code_rejected(client):
    res1 = client.post("/api/courses", json={"code": "MATH101", "title": "Calculus I", "seats": 30})
    assert res1.status_code == 201

    res2 = client.post("/api/courses", json={"code": "MATH101", "title": "Duplicate Calculus", "seats": 20})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_invalid_course_input(client):
    # Seats must be >= 1
    res = client.post("/api/courses", json={"code": "BAD1", "title": "Bad Seats", "seats": 0})
    assert res.status_code == 422

    # Blank title
    res2 = client.post("/api/courses", json={"code": "BAD2", "title": "   ", "seats": 5})
    assert res2.status_code == 422

def test_create_and_list_student(client):
    res = client.post("/api/students", json={"name": "Alice Johnson", "email": "alice@example.com"})
    assert res.status_code == 201
    stu = res.json()
    assert stu["name"] == "Alice Johnson"
    assert stu["email"] == "alice@example.com"

    res_list = client.get("/api/students")
    assert res_list.status_code == 200
    students = res_list.json()
    assert any(s["email"] == "alice@example.com" for s in students)

def test_duplicate_student_email_rejected(client):
    res1 = client.post("/api/students", json={"name": "Bob Smith", "email": "bob@example.com"})
    assert res1.status_code == 201

    res2 = client.post("/api/students", json={"name": "Bob Duplicate", "email": "bob@example.com"})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

def test_registration_flow_and_capacity_limits(client):
    # Create 1 course with capacity of 1
    c_res = client.post("/api/courses", json={"code": "LIMIT1", "title": "Limited Seminar", "seats": 1})
    assert c_res.status_code == 201
    c_id = c_res.json()["id"]

    # Create 2 students
    s1_res = client.post("/api/students", json={"name": "Student One", "email": "s1@example.com"})
    s2_res = client.post("/api/students", json={"name": "Student Two", "email": "s2@example.com"})
    s1_id = s1_res.json()["id"]
    s2_id = s2_res.json()["id"]

    # 1. Register student 1 -> Should succeed
    reg1 = client.post("/api/registrations", json={"student_id": s1_id, "course_id": c_id})
    assert reg1.status_code == 201
    reg1_id = reg1.json()["id"]

    # 2. Duplicate registration attempt -> Should fail with 409
    dup_reg = client.post("/api/registrations", json={"student_id": s1_id, "course_id": c_id})
    assert dup_reg.status_code == 409
    assert "already registered" in dup_reg.json()["detail"]

    # 3. Capacity limit test: Student 2 attempts to register in full course -> Should fail with 409
    full_reg = client.post("/api/registrations", json={"student_id": s2_id, "course_id": c_id})
    assert full_reg.status_code == 409
    assert "full" in full_reg.json()["detail"]

    # 4. Check roster
    roster_res = client.get(f"/api/courses/{c_id}/students")
    assert roster_res.status_code == 200
    roster = roster_res.json()
    assert len(roster) == 1
    assert roster[0]["student_id"] == s1_id

    # 5. Check course listing shows 0 available seats
    c_check = client.get("/api/courses").json()
    matched = [c for c in c_check if c["id"] == c_id][0]
    assert matched["enrolled_count"] == 1
    assert matched["available_seats"] == 0

    # 6. Cancel registration for Student 1 -> Seat freed
    cancel_res = client.delete(f"/api/registrations/{reg1_id}")
    assert cancel_res.status_code == 200

    # Verify course now has 1 available seat
    c_check2 = client.get("/api/courses").json()
    matched2 = [c for c in c_check2 if c["id"] == c_id][0]
    assert matched2["enrolled_count"] == 0
    assert matched2["available_seats"] == 1

    # 7. Student 2 can now register successfully
    reg2 = client.post("/api/registrations", json={"student_id": s2_id, "course_id": c_id})
    assert reg2.status_code == 201

def test_delete_course_cascades_registrations(client):
    # Setup course and student
    c = client.post("/api/courses", json={"code": "DEL101", "title": "To Be Deleted", "seats": 5}).json()
    s = client.post("/api/students", json={"name": "Delete Tester", "email": "del@example.com"}).json()

    reg = client.post("/api/registrations", json={"student_id": s["id"], "course_id": c["id"]}).json()

    # Delete the course
    del_res = client.delete(f"/api/courses/{c['id']}")
    assert del_res.status_code == 200

    # Registrations list should no longer include this registration
    all_regs = client.get("/api/registrations").json()
    assert not any(r["id"] == reg["id"] for r in all_regs)

def test_delete_student_cascades_registrations(client):
    # Setup course and student
    c = client.post("/api/courses", json={"code": "STDEL101", "title": "Student Delete Test", "seats": 5}).json()
    s = client.post("/api/students", json={"name": "Will Be Deleted", "email": "willbedeleted@example.com"}).json()

    reg = client.post("/api/registrations", json={"student_id": s["id"], "course_id": c["id"]}).json()

    # Delete the student
    del_res = client.delete(f"/api/students/{s['id']}")
    assert del_res.status_code == 200

    # Verify student is removed
    all_students = client.get("/api/students").json()
    assert not any(st["id"] == s["id"] for st in all_students)

    # Verify registration is removed
    all_regs = client.get("/api/registrations").json()
    assert not any(r["id"] == reg["id"] for r in all_regs)
