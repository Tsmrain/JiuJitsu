#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
import shutil
from playwright.sync_api import sync_playwright

DOCS_DIR = "/Users/santiago/Desktop/JiuJitsu-main/docs/visual_evidence/transition-2c"
TMP_DIR = "/tmp/baseline_after"

os.makedirs(f"{DOCS_DIR}/before", exist_ok=True)
os.makedirs(f"{DOCS_DIR}/after", exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# 1. Setup 'before' evidence from transition-2b.1
source_b1 = "/Users/santiago/Desktop/JiuJitsu-main/docs/visual_evidence/transition-2b.1/after"
if os.path.exists(f"{source_b1}/feedback.png"):
    shutil.copyfile(f"{source_b1}/feedback.png", f"{DOCS_DIR}/before/feedback.png")
if os.path.exists(f"{source_b1}/admin.png"):
    shutil.copyfile(f"{source_b1}/admin.png", f"{DOCS_DIR}/before/profesor.png")
print("Setup 'before' screenshots in docs/visual_evidence/transition-2c/before/")

# 2. Get user payloads via API
def get_user_data(username, password):
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/auth/login",
        data=json.dumps({"username_or_email": username, "password": password}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

admin_data = get_user_data("admin", "admin123")
mike_data = get_user_data("mike", "password123")
santi_data = get_user_data("santi", "password123")

print("Users logged in successfully:", admin_data["username"], mike_data["username"], santi_data["username"])

# 3. Fetch real evaluation data from API
eval_id = "b5a01854-3f66-47f4-b415-4e11da4d41a1"
eval_req = urllib.request.Request(
    f"http://localhost:8000/api/v1/evaluaciones/{eval_id}",
    headers={"Authorization": f"Bearer {santi_data['token']}"}
)
with urllib.request.urlopen(eval_req) as resp:
    eval_data = json.loads(resp.read().decode("utf-8"))

print("Fetched evaluation data:", eval_data["id"], eval_data["similitud"])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 960})
    
    # -------------------------------------------------------------------------
    # A. FeedbackView (Student 2x2 layout)
    # -------------------------------------------------------------------------
    print("Capturing after/feedback.png...")
    page.goto("http://localhost:5173")
    page.wait_for_selector(".app-container")
    time.sleep(1)
    
    tecnica_info = {
        "id": eval_data["tecnica_id"],
        "nombre": "Mount Escape",
        "profesorRef": "Coach Mike Baigorria"
    }
    
    page.evaluate("""({ studentUser, result, tecnica }) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[5]: setUser(studentUser)
        hooks[5].queue.dispatch(studentUser);
        // hooks[2]: setResult(result)
        hooks[2].queue.dispatch(result);
        // hooks[3]: setSelectedTecnica(tecnica)
        hooks[3].queue.dispatch(tecnica);
        // hooks[0]: setAppState('FEEDBACK')
        hooks[0].queue.dispatch('FEEDBACK');
    }""", {"studentUser": santi_data, "result": eval_data, "tecnica": tecnica_info})
    
    time.sleep(2)
    feedback_path = f"{DOCS_DIR}/after/feedback.png"
    page.screenshot(path=feedback_path, full_page=True)
    shutil.copyfile(feedback_path, f"{TMP_DIR}/feedback.png")
    print("Saved:", feedback_path)

    # -------------------------------------------------------------------------
    # B. ProfesorTecnicas (Professor View with Badges and Summary)
    # -------------------------------------------------------------------------
    print("Capturing after/profesor.png...")
    page.evaluate("""(profUser) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[5]: setUser(profUser)
        hooks[5].queue.dispatch(profUser);
        // hooks[0]: setAppState('PROFESOR_PANEL')
        hooks[0].queue.dispatch('PROFESOR_PANEL');
    }""", mike_data)
    
    time.sleep(2)
    profesor_path = f"{DOCS_DIR}/after/profesor.png"
    page.screenshot(path=profesor_path, full_page=True)
    shutil.copyfile(profesor_path, f"{TMP_DIR}/profesor.png")
    print("Saved:", profesor_path)

    # -------------------------------------------------------------------------
    # C. ProfesorTecnicas Detail Modal (Clicked 'View Details')
    # -------------------------------------------------------------------------
    print("Capturing after/profesor_modal.png...")
    # Click the first "View Details" button
    view_details_btn = page.query_selector("button:has-text('View Details')")
    if view_details_btn:
        view_details_btn.click()
        time.sleep(1)
        modal_path = f"{DOCS_DIR}/after/profesor_modal.png"
        page.screenshot(path=modal_path)
        shutil.copyfile(modal_path, f"{TMP_DIR}/profesor_modal.png")
        print("Saved:", modal_path)
        # Close modal
        close_btn = page.query_selector(".modal-actions button:has-text('Close')")
        if close_btn:
            close_btn.click()
            time.sleep(0.5)

    # -------------------------------------------------------------------------
    # D. StudentProgress (My Progress view with videos)
    # -------------------------------------------------------------------------
    print("Capturing after/student_progress.png...")
    page.evaluate("""(studentUser) => {
        const el = document.querySelector('.app-container');
        const key = Object.keys(el).find(k => k.startsWith('__reactFiber'));
        let fiber = el[key];
        while (fiber && fiber.type?.name !== 'App') fiber = fiber.return;
        
        let hooks = [];
        let h = fiber.memoizedState;
        while (h) { hooks.push(h); h = h.next; }
        
        // hooks[5]: setUser(studentUser)
        hooks[5].queue.dispatch(studentUser);
        // hooks[0]: setAppState('STUDENT_PROGRESS')
        hooks[0].queue.dispatch('STUDENT_PROGRESS');
    }""", santi_data)
    
    time.sleep(2)
    progress_path = f"{DOCS_DIR}/after/student_progress.png"
    page.screenshot(path=progress_path, full_page=True)
    shutil.copyfile(progress_path, f"{TMP_DIR}/student_progress.png")
    print("Saved:", progress_path)

    browser.close()
    print("All screenshots captured and saved successfully.")

