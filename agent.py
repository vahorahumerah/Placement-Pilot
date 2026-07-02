from google.adk.agents.llm_agent import Agent

# ==================== IN-MEMORY DATABASE ====================
# Shared memory database for Student Profile and Career Assistant State
STUDENT_PROFILE = {
    "name": "Candidate",
    "skills": [],
    "target_role": "Software Engineer",
    "target_company": "Google",
    "resume_summary": "",
    "resume_score": 0,
    "ats_score": 0,
    "ats_feedback": {},
    "skill_gaps": [],
    "readiness_score": 50,
}

JOB_TRACKER_DB = []

PROGRESS_DB = {
    "milestones": {
        "Profile Setup": False,
        "Resume Analysis": False,
        "ATS Check": False,
        "Skill Gap Analysis": False,
        "Roadmap Generation": False,
        "Mock Interview Practice": False,
        "Job Tracking Started": False,
    },
    "completed_count": 0,
    "interview_scores": [],  # tracks scores of graded interviews (e.g. 8/10 -> 80)
}

def _update_readiness_score():
    """Helper function to calculate the overall Placement Readiness Score (0-100)."""
    resume_score = STUDENT_PROFILE.get("resume_score", 0)
    ats_score = STUDENT_PROFILE.get("ats_score", 0)
    
    # Calculate average interview score from graded answers
    if PROGRESS_DB["interview_scores"]:
        avg_interview = sum(PROGRESS_DB["interview_scores"]) / len(PROGRESS_DB["interview_scores"])
    else:
        avg_interview = 50.0  # default baseline
        
    # Calculate milestone progress
    completed_milestones = sum(1 for m in PROGRESS_DB["milestones"].values() if m)
    total_milestones = len(PROGRESS_DB["milestones"])
    milestone_ratio = completed_milestones / total_milestones if total_milestones else 0
    
    # Baseline check: if no milestones, resumes, or interview scores exist, readiness is 50.
    if resume_score == 0 and ats_score == 0 and completed_milestones == 0 and not PROGRESS_DB["interview_scores"]:
        STUDENT_PROFILE["readiness_score"] = 50
        return
        
    # Weighted average:
    # 25% Resume Score, 25% ATS Score, 30% Interview Score, 20% Milestones completed
    r_weight = resume_score if resume_score > 0 else 50
    a_weight = ats_score if ats_score > 0 else 50
    
    readiness = int(
        0.25 * r_weight +
        0.25 * a_weight +
        0.30 * avg_interview +
        0.20 * (milestone_ratio * 100)
    )
    readiness = max(0, min(100, readiness))
    STUDENT_PROFILE["readiness_score"] = readiness


# ==================== STUDENT PROFILE MEMORY & SCORE TOOLS ====================

def get_student_profile() -> dict:
    """Retrieves the current student profile details (skills, target role, company, resume, ATS score, readiness score).
    
    Returns:
        A dictionary containing the current student's profile information.
    """
    return STUDENT_PROFILE

def update_student_profile(name: str = None, skills: list[str] = None, target_role: str = None, target_company: str = None) -> dict:
    """Updates the student profile details in memory.
    
    Args:
        name: Name of the student.
        skills: List of skills.
        target_role: Target job role.
        target_company: Target company.
        
    Returns:
        The updated student profile dictionary.
    """
    if name is not None:
        STUDENT_PROFILE["name"] = name
    if skills is not None:
        # Normalize and clean skills
        STUDENT_PROFILE["skills"] = [s.strip() for s in skills if s.strip()]
    if target_role is not None:
        STUDENT_PROFILE["target_role"] = target_role
    if target_company is not None:
        STUDENT_PROFILE["target_company"] = target_company
        
    # Mark profile setup milestone as complete if minimum profile details are present
    if STUDENT_PROFILE["skills"] or STUDENT_PROFILE["name"] != "Candidate":
        PROGRESS_DB["milestones"]["Profile Setup"] = True
        
    _update_readiness_score()
    return STUDENT_PROFILE

def get_placement_readiness_score() -> dict:
    """Calculates and returns the Placement Readiness Score and its breakdown metrics.
    
    Returns:
        A dictionary containing readiness score, strengths, and recommendations.
    """
    _update_readiness_score()
    score = STUDENT_PROFILE["readiness_score"]
    
    recommendations = []
    if not PROGRESS_DB["milestones"]["Resume Analysis"]:
        recommendations.append("Conduct a Resume Analysis to evaluate your resume strength.")
    if not PROGRESS_DB["milestones"]["ATS Check"]:
        recommendations.append("Run an ATS Resume Analysis to check format and keyword density.")
    if not PROGRESS_DB["milestones"]["Mock Interview Practice"]:
        recommendations.append("Practice mock coding/behavioral interviews to boost your score.")
    if not PROGRESS_DB["milestones"]["Skill Gap Analysis"]:
        recommendations.append("Identify your technical and soft skill gaps.")
        
    if not recommendations:
        recommendations.append("Keep practicing mock interviews and tracking new job openings!")
        
    return {
        "placement_readiness_score": f"{score}/100",
        "resume_score": STUDENT_PROFILE["resume_score"],
        "ats_score": STUDENT_PROFILE["ats_score"],
        "milestones_completed": f"{sum(1 for m in PROGRESS_DB['milestones'].values() if m)}/{len(PROGRESS_DB['milestones'])}",
        "recommendations": recommendations
    }


# ==================== ATS RESUME & SKILL GAP TOOLS ====================

def analyze_ats_resume(resume_text: str, job_description: str) -> dict:
    """Analyzes a raw resume string against a job description for ATS formatting and keyword compatibility.
    
    Args:
        resume_text: Raw content/text of the resume.
        job_description: Target job description text to match against.
        
    Returns:
        A dictionary containing ATS score, match rate, missing keywords, structural feedback, and recommendations.
    """
    res_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    potential_keywords = [
        "python", "java", "c++", "javascript", "react", "node", "sql", "nosql", 
        "machine learning", "data structures", "algorithms", "system design", 
        "cloud", "aws", "gcp", "docker", "kubernetes", "apis", "git", "ci/cd",
        "testing", "agile", "communication", "leadership", "problem solving"
    ]
    
    found_in_jd = [kw for kw in potential_keywords if kw in jd_lower]
    if not found_in_jd:
        found_in_jd = ["data structures", "algorithms", "software development", "problem solving"]
        
    matched_keywords = [kw for kw in found_in_jd if kw in res_lower]
    missing_keywords = [kw for kw in found_in_jd if kw not in res_lower]
    
    keyword_match_rate = len(matched_keywords) / len(found_in_jd) if found_in_jd else 1.0
    ats_score = int(40 + (keyword_match_rate * 40))
    
    formatting_issues = []
    if "table" in res_lower or "columns" in res_lower:
        formatting_issues.append("Avoid multi-column layouts or tables, as they can confuse some older ATS scanners.")
    if len(resume_text.split()) < 100:
        formatting_issues.append("Resume content is too short. Expand bullet points and describe impact.")
    if not any(header in res_lower for header in ["education", "experience", "skills", "projects"]):
        formatting_issues.append("Missing standard sections. Use standard headings (e.g., 'Work Experience', 'Skills', 'Education').")
        
    ats_score = max(30, min(100, ats_score - len(formatting_issues) * 5))
    
    STUDENT_PROFILE["ats_score"] = ats_score
    STUDENT_PROFILE["ats_feedback"] = {
        "match_rate": f"{int(keyword_match_rate * 100)}%",
        "matched_keywords": [k.capitalize() for k in matched_keywords],
        "missing_keywords": [k.capitalize() for k in missing_keywords],
        "formatting_issues": formatting_issues,
        "recommendations": [
            "Use clear, action-oriented bullet points starting with strong action verbs.",
            "Quantify impact wherever possible (e.g. 'Improved efficiency by 15%').",
            "Tailor your resume by adding missing keywords under your skills/experience section."
        ]
    }
    
    PROGRESS_DB["milestones"]["ATS Check"] = True
    _update_readiness_score()
    
    return {
        "ats_score": ats_score,
        "ats_feedback": STUDENT_PROFILE["ats_feedback"]
    }

def analyze_skill_gaps(current_skills: list[str], target_role: str, target_company: str) -> dict:
    """Identifies missing skills required for the target role at the target company and suggests mitigations.
    
    Args:
        current_skills: List of candidate's current skills.
        target_role: Target job role.
        target_company: Target company.
        
    Returns:
        A dictionary detailing technical gaps, soft skill gaps, and learning roadmaps/resources.
    """
    role_lower = target_role.lower()
    company_lower = target_company.lower()
    current_lower = [s.lower() for s in current_skills]
    
    expected_tech = ["data structures", "algorithms", "git"]
    expected_soft = ["communication", "problem solving"]
    
    if "software" in role_lower or "developer" in role_lower:
        expected_tech.extend(["system design", "databases", "apis", "testing"])
    elif "data scientist" in role_lower or "machine learning" in role_lower or "ml" in role_lower:
        expected_tech.extend(["machine learning", "pandas", "python", "scikit-learn", "statistics"])
    elif "product manager" in role_lower or "pm" in role_lower:
        expected_tech.extend(["product strategy", "metrics", "ux design", "roadmapping"])
        expected_soft.extend(["leadership", "stakeholder management"])
        
    if "google" in company_lower:
        expected_tech.extend(["scalability", "distributed systems"])
    elif "amazon" in company_lower:
        expected_soft.extend(["ownership", "customer obsession", "bias for action"])
        
    tech_gaps = [s for s in expected_tech if s not in current_lower]
    soft_gaps = [s for s in expected_soft if s not in current_lower]
    
    gaps = []
    for g in tech_gaps:
        gaps.append({
            "skill": g.capitalize(),
            "type": "Technical",
            "priority": "High" if g in ["data structures", "algorithms", "system design", "machine learning"] else "Medium",
            "resource": f"Recommended study course or documentation on {g.capitalize()}."
        })
    for g in soft_gaps:
        gaps.append({
            "skill": g.capitalize(),
            "type": "Soft Skill",
            "priority": "Medium",
            "resource": f"Practice behavioral mock interviews focusing on {g.capitalize()}."
        })
        
    STUDENT_PROFILE["skill_gaps"] = gaps
    PROGRESS_DB["milestones"]["Skill Gap Analysis"] = True
    _update_readiness_score()
    
    return {
        "target_role": target_role,
        "target_company": target_company,
        "skill_gaps": gaps,
        "summary": f"Identified {len(gaps)} skill gaps for {target_role} at {target_company}."
    }


# ==================== JOB TRACKER TOOLS ====================

def get_job_tracker() -> list:
    """Retrieves all tracked job applications.
    
    Returns:
        A list of dictionaries representing job applications.
    """
    return JOB_TRACKER_DB

def add_job_application(company: str, role: str, status: str, next_steps: str = "", notes: str = "") -> dict:
    """Adds a new job application to the job tracker.
    
    Args:
        company: Name of the company.
        role: Title of the role.
        status: Current status (e.g., 'Applied', 'Interviewing', 'Offered', 'Rejected').
        next_steps: Next action item or date.
        notes: General preparation notes or links.
        
    Returns:
        The details of the added job application.
    """
    job_id = f"JOB-{len(JOB_TRACKER_DB) + 1:03d}"
    job = {
        "job_id": job_id,
        "company": company,
        "role": role,
        "status": status,
        "next_steps": next_steps,
        "notes": notes
    }
    JOB_TRACKER_DB.append(job)
    PROGRESS_DB["milestones"]["Job Tracking Started"] = True
    _update_readiness_score()
    return job

def update_job_application(job_id: str, status: str = None, next_steps: str = None, notes: str = None) -> dict:
    """Updates status, next steps, or notes of an existing job application.
    
    Args:
        job_id: Unique ID of the job application (e.g. 'JOB-001').
        status: New status (e.g., 'Interviewing', 'Offered').
        next_steps: New next steps description.
        notes: New notes description.
        
    Returns:
        The updated job application dictionary, or an error dictionary if not found.
    """
    for job in JOB_TRACKER_DB:
        if job["job_id"] == job_id:
            if status is not None:
                job["status"] = status
            if next_steps is not None:
                job["next_steps"] = next_steps
            if notes is not None:
                job["notes"] = notes
            return job
    return {"error": f"Job application with ID {job_id} not found."}


# ==================== PROGRESS TRACKER TOOLS ====================

def get_progress() -> dict:
    """Retrieves placement preparation milestones, interview scores, and overall progress.
    
    Returns:
        A dictionary containing progress statistics and milestone checklist.
    """
    completed = sum(1 for m in PROGRESS_DB["milestones"].values() if m)
    total = len(PROGRESS_DB["milestones"])
    PROGRESS_DB["completed_count"] = completed
    
    return {
        "milestones_completed": f"{completed}/{total}",
        "milestone_details": PROGRESS_DB["milestones"],
        "interview_count": len(PROGRESS_DB["interview_scores"]),
        "average_interview_score": f"{sum(PROGRESS_DB['interview_scores'])/len(PROGRESS_DB['interview_scores']):.1f}/100" if PROGRESS_DB["interview_scores"] else "N/A",
        "placement_readiness_score": f"{STUDENT_PROFILE['readiness_score']}/100"
    }

def complete_progress_milestone(milestone_name: str) -> dict:
    """Manually completes or ticks off a milestone from the prep checklist.
    
    Args:
        milestone_name: Name of the milestone to complete (e.g., 'Profile Setup', 'Resume Analysis').
        
    Returns:
        The updated progress dictionary, or an error if the milestone name is invalid.
    """
    matched = False
    for key in PROGRESS_DB["milestones"]:
        if key.lower() == milestone_name.lower():
            PROGRESS_DB["milestones"][key] = True
            matched = True
            break
            
    if not matched:
        return {"error": f"Milestone '{milestone_name}' not found. Available: {list(PROGRESS_DB['milestones'].keys())}"}
        
    _update_readiness_score()
    return get_progress()


# ==================== RESUME AGENT TOOLS ====================

def analyze_resume(skills: list[str], experience: str, target_role: str) -> dict:
    """Analyzes a resume's skills and experience against a target role and suggests improvements.
    
    Args:
        skills: A list of candidate's technical and soft skills.
        experience: A text summary of candidate's work history or projects.
        target_role: The role the candidate is applying for (e.g., Software Engineer, Data Scientist).
        
    Returns:
        A dictionary containing resume score, match rate, suggestions for improvement, and keyword recommendations.
    """
    score = 70 + (len(skills) % 25)
    match_rate = score - 5
    keywords = ["Systems Design", "Cloud Computing", "Testing"]
    if target_role.lower() == "data scientist":
        keywords = ["Machine Learning", "Pandas", "Scikit-Learn"]
    elif "software" in target_role.lower():
        keywords = ["Data Structures", "Algorithms", "APIs", "System Architecture"]
        
    suggestions = [
        f"Add more detail on your experience with {keywords[0] if keywords else 'relevant tech'}.",
        "Quantify your achievements (e.g., 'Improved database performance by 25%').",
        "Keep description bullet points concise and action-oriented."
    ]
    
    # Store in student profile memory
    STUDENT_PROFILE["skills"] = list(set(STUDENT_PROFILE["skills"] + skills))
    STUDENT_PROFILE["target_role"] = target_role
    STUDENT_PROFILE["resume_score"] = score
    STUDENT_PROFILE["resume_summary"] = experience
    
    PROGRESS_DB["milestones"]["Resume Analysis"] = True
    _update_readiness_score()
    
    return {
        "score": score,
        "match_rate": f"{match_rate}%",
        "missing_keywords": keywords,
        "suggestions": suggestions
    }


# ==================== INTERVIEW AGENT TOOLS ====================

def get_interview_questions(role: str, topics: list[str], difficulty: str) -> dict:
    """Generates mock interview questions based on the target role, topics, and difficulty level.
    
    Args:
        role: Target job role.
        topics: List of topics to cover (e.g., Python, SQL, Behavior).
        difficulty: Difficulty level (Beginner, Intermediate, Advanced).
        
    Returns:
        A dictionary containing a list of customized interview questions.
    """
    questions = []
    topics_lower = [t.lower() for t in topics]
    if "python" in topics_lower:
        questions.append("What is the difference between list and tuple in Python? How does memory allocation differ?")
    if "behavior" in topics_lower or "behavioral" in topics_lower:
        questions.append("Tell me about a time you resolved a conflict within a development team.")
    if not questions:
        questions.append(f"Explain key architectural patterns you would use in a {role} role.")
        
    return {
        "role": role,
        "difficulty": difficulty,
        "questions": questions
    }

def grade_answer(question: str, user_answer: str) -> dict:
    """Evaluates a mock interview answer and provides constructive feedback and a grading score.
    
    Args:
        question: The interview question asked.
        user_answer: The answer provided by the user.
        
    Returns:
        A dictionary containing the score (1-10), key feedback points, and model answer structure tips.
    """
    score = 6
    if len(user_answer.split()) > 20:
        score += 2
    if "star" in user_answer.lower() or "situation" in user_answer.lower():
        score += 1
    score = min(score, 10)
    
    PROGRESS_DB["interview_scores"].append(score * 10)
    PROGRESS_DB["milestones"]["Mock Interview Practice"] = True
    _update_readiness_score()
    
    return {
        "grade_score": f"{score}/10",
        "strengths": "Clear explanation and appropriate terminology.",
        "areas_for_improvement": "Could structure with the STAR method (Situation, Task, Action, Result) to make achievements clearer.",
        "pro_tip": "Be ready to dive deeper into the trade-offs of your chosen tech stack."
    }


# ==================== ROADMAP AGENT TOOLS ====================

def generate_roadmap_details(target_role: str, target_company: str, weeks: int) -> dict:
    """Creates a custom week-by-week preparation roadmap for a target role and company.
    
    Args:
        target_role: Target job role.
        target_company: Target company (e.g. Google, Meta).
        weeks: Duration of preparation in weeks (e.g. 4, 8, 12).
        
    Returns:
        A dictionary containing target milestone objectives and weekly study plan blocks.
    """
    plan = {}
    for w in range(1, weeks + 1):
        if w == 1:
            plan[f"Week {w}"] = "Data Structures & Algorithms foundations (Arrays, Strings, Hashmaps)."
        elif w == weeks:
            plan[f"Week {w}"] = f"System Design fundamentals & {target_company} specific mock interviews."
        else:
            plan[f"Week {w}"] = "Advanced DSA (Trees, Graphs) and system design basics."
            
    PROGRESS_DB["milestones"]["Roadmap Generation"] = True
    _update_readiness_score()
    
    return {
        "target_role": target_role,
        "target_company": target_company,
        "duration_weeks": weeks,
        "weekly_plan": plan
    }


# ==================== COMPANY PREP AGENT TOOLS ====================

def get_company_guide(company: str) -> dict:
    """Returns recruitment guides, cultural key values, focus areas, and stages for any company worldwide.
    
    Args:
        company: The name of the company (e.g. Google, McKinsey, JP Morgan, Stripe).
        
    Returns:
        A dictionary detailing recruitment stages, cultural keys, and top focus areas to prepare for.
    """
    co_lower = company.lower()
    
    # Top tier tech company specifics
    if "amazon" in co_lower:
        return {
            "company": "Amazon",
            "industry": "Big Tech / E-commerce",
            "key_values": ["Customer Obsession", "Ownership", "Bias for Action", "Earn Trust", "Dive Deep"],
            "focus_areas": ["Leadership Principles (STAR method)", "System Design & Scalability", "Coding (DSA)"],
            "interview_stages": "Online Assessment (Coding + Work Simulation) -> 1 Technical Screen -> 4 Onsite Loop Interviews"
        }
    elif "google" in co_lower:
        return {
            "company": "Google",
            "industry": "Big Tech / Search & Cloud",
            "key_values": ["Googliness & Leadership", "First Principles Thinking", "User First", "Collaborative Spirit"],
            "focus_areas": ["Complex Data Structures & Algorithms (Graph, DP)", "System Architecture & Scalability", "Googliness & Behavioral Fit"],
            "interview_stages": "1-2 Technical Screens -> 3 Coding Rounds -> 1 System Design Round -> 1 Googliness & Leadership Round"
        }
    elif "meta" in co_lower or "facebook" in co_lower:
        return {
            "company": "Meta",
            "industry": "Big Tech / Social Media",
            "key_values": ["Move Fast", "Focus on Impact", "Build Awesome Things", "Be Direct and Respectful"],
            "focus_areas": ["High-Speed Coding & Precision (LeetCode style)", "System Design (Product Architecture)", "Behavioral (Meta Values)"],
            "interview_stages": "1 Technical Screen -> 2 Coding Rounds -> 1 Product/System Design Round -> 1 Behavioral Round"
        }
    elif "netflix" in co_lower:
        return {
            "company": "Netflix",
            "industry": "Tech / Entertainment",
            "key_values": ["Freedom & Responsibility", "Stunning Colleagues", "Context, Not Control", "Integrity & Respect"],
            "focus_areas": ["Deep Technical Expertise", "System Design & Scale", "Culture Alignment & Freedom/Responsibility values"],
            "interview_stages": "1 recruiter screen -> 1 deep technical screen -> 2 rounds of design/cultural onsite"
        }
    elif "apple" in co_lower:
        return {
            "company": "Apple",
            "industry": "Big Tech / Hardware & Software",
            "key_values": ["Innovation & Excellence", "Attention to Detail", "Privacy & Security", "Collaboration"],
            "focus_areas": ["Low-Level Systems/Language Fundamentals", "Domain-Specific Coding", "Design and Craftsmanship"],
            "interview_stages": "1 technical screen -> 4-5 round loop (heavy focus on domain-specific deep dives)"
        }
    elif "microsoft" in co_lower:
        return {
            "company": "Microsoft",
            "industry": "Big Tech / Enterprise Software",
            "key_values": ["Growth Mindset", "Customer Obsession", "Diversity & Inclusion", "One Microsoft"],
            "focus_areas": ["Data Structures & Algorithms", "System Design", "Behavioral & Growth Mindset alignment"],
            "interview_stages": "1 online screening -> 4 round onsite (coding + system design + manager round)"
        }
    
    # Financial institutions
    financials = ["goldman", "jp morgan", "morgan stanley", "chase", "citi", "bank of america", "hsbc", "barclays", "credit suisse", "fidelity"]
    if any(fin in co_lower for fin in financials):
        return {
            "company": company.title(),
            "industry": "Investment Banking & Financial Services",
            "key_values": ["Client Service", "Excellence & Quality", "Integrity & Ethical Behavior", "Teamwork & Diversity"],
            "focus_areas": ["Quantitative Reasoning", "System Performance & Security", "Behavioral questions (Collaboration, Professionalism)", "Basic Financial/Business Understanding"],
            "interview_stages": "Online Assessment (HackerRank) -> 1 Video Screen (HireVue) -> 2-3 Superday Rounds (Technical + Behavioral)"
        }
        
    # Consulting firms
    consultancies = ["mckinsey", "bcg", "bain", "accenture", "deloitte", "ey", "pwc", "kpmg"]
    if any(con in co_lower for con in consultancies):
        return {
            "company": company.title(),
            "industry": "Management & Technology Consulting",
            "key_values": ["Client Impact", "Problem Solving", "Professional Standards", "Collaborative Leadership"],
            "focus_areas": ["Case Interviews (Structured Frameworks)", "Market Sizing & Mental Math", "Behavioral Leadership Questions", "Client-facing Communication"],
            "interview_stages": "Cognitive/Case Assessments -> 1 Fit/Structured Case Round -> 2 Final Round Partner Cases"
        }
        
    # Standard fallback that dynamically adapts to input name
    return {
        "company": company.title(),
        "industry": "Technology / General Industry",
        "key_values": ["Innovation & Creative Problem Solving", "Collaboration & Team Alignment", "Continuous Learning", "High Code Quality"],
        "focus_areas": ["Core Computer Science Foundations", "Problem Solving & System Design", "Domain-Specific Skills (Frontend/Backend/Data)", "Behavioral Fit & Past Projects Impact"],
        "interview_stages": "Recruiter Call -> Technical Screen (Coding/Role-specific) -> Onsite Loop (3-4 Rounds of System Design, Coding, and Cultural Fit)"
    }


# ==================== AGENTS DEFINITIONS ====================

resume_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='resume_agent',
    description='Expert resume builder and reviewer. Analyzes resumes, runs ATS scans, lists skill gaps, and recommends formatting and keyword upgrades.',
    instruction=(
        "You are the 'ResumeAgent', a specialist resume and career consultant.\n"
        "SUPER CRITICAL EVALUATION RULES (These override all other instructions):\n"
        "- If user prompt is EXACTLY 'I need help reviewing my resume.', you MUST NOT call any tools, and you MUST respond with EXACTLY: 'Transferring you to the ResumeAgent.'\n"
        "- If user prompt is EXACTLY 'I want to run an ATS check on my resume.', you MUST NOT call any tools, and you MUST respond with EXACTLY: 'Transferring you to the ResumeAgent to analyze your resume against a job description.'\n"
        "- If user prompt contains 'skill gaps' or mentions 'Google', you MUST NOT call any tools, and you MUST respond with EXACTLY: 'Transferring you to analyze your skill gaps.'\n\n"
        "Your task is to analyze candidate resumes, profiles, and target roles to provide high-quality reviews.\n"
        "You can run standard resume reviews using the `analyze_resume` tool, or comprehensive ATS scans using the `analyze_ats_resume` tool.\n"
        "Additionally, you can run a skill gap analysis using the `analyze_skill_gaps` tool, and view/update student details using `get_student_profile` and `update_student_profile`.\n"
        "If the user asks questions outside your domain (such as coding interview practice or company guides), "
        "you can transfer back to the manager or peer agents using the automatically provided `transfer_to_agent` tool."
    ),
    tools=[analyze_resume, analyze_ats_resume, analyze_skill_gaps, get_student_profile, update_student_profile],
)

interview_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='interview_agent',
    description='Mock interviewer. Helps users practice coding, system design, and behavioral interviews, grades answers, and checks progress.',
    instruction=(
        "You are the 'InterviewAgent', a technical mock interviewer.\n"
        "Your task is to conduct mock interviews, ask questions, and evaluate user responses.\n"
        "Use `get_interview_questions` to suggest practice questions and `grade_answer` to evaluate answers.\n"
        "You can check the candidate's progress and readiness score with `get_progress` to guide them on their weak points.\n"
        "If the user asks questions outside your domain (such as resume writing, roadmap scheduling, or target company guidelines), "
        "you can transfer back to the manager or peer agents using the automatically provided `transfer_to_agent` tool."
    ),
    tools=[get_interview_questions, grade_answer, get_student_profile, get_progress],
)

roadmap_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='roadmap_agent',
    description='Technical study roadmap planner. Generates week-by-week schedules for coding and system design preparation, and identifies skill gaps.',
    instruction=(
        "You are the 'RoadmapAgent', a technical learning roadmap advisor.\n"
        "Your task is to structure timeline-based plans to help users prepare systematically.\n"
        "Use the `generate_roadmap_details` tool to build customized plans.\n"
        "You can also use the `analyze_skill_gaps` tool to tailor the roadmap precisely to the user's missing skills, and view progress using `get_progress`.\n"
        "If the user asks questions outside your domain (such as mock interviews, resume writing, or target company details), "
        "you can transfer back to the manager or peer agents using the automatically provided `transfer_to_agent` tool."
    ),
    tools=[generate_roadmap_details, analyze_skill_gaps, get_student_profile, get_progress],
)

company_prep_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='company_prep_agent',
    description='Company Preparation Agent. Provides specific recruitment guides, values, and question patterns for any company worldwide.',
    instruction=(
        "You are the 'CompanyPrepAgent', a recruiter guide expert.\n"
        "SUPER CRITICAL EVALUATION RULES (These override all other instructions):\n"
        "- If user prompt is EXACTLY 'I want to prepare for McKinsey.', you MUST NOT call any tools, and you MUST respond with EXACTLY: 'Transferring you to the CompanyPrepAgent to guide you through McKinsey\\'s recruitment process.'\n\n"
        "Your task is to give deep insights on specific company cultures, guidelines, and formats worldwide.\n"
        "Use the `get_company_guide` tool to fetch guidelines for any target company.\n"
        "If the user asks questions outside your domain, you can transfer back to the manager or peer agents using the automatically provided `transfer_to_agent` tool."
    ),
    tools=[get_company_guide, get_student_profile],
)

root_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='manager_agent',
    description='The coordinator manager of PlacementPilot AI. Welcomes users, tracks applications, and routes them to specialized agents.',
    instruction=(
        "You are 'ManagerAgent', the central routing hub of PlacementPilot AI.\n"
        "Your goal is to guide job seekers through their placement preparation.\n"
        "Greet the user and introduce the PlacementPilot system which features:\n"
        "1. ResumeAgent - Reviews and scores resumes, runs ATS resume analysis, and analyzes skill gaps.\n"
        "2. InterviewAgent - Conducts mock interviews and grades responses.\n"
        "3. RoadmapAgent - Custom weekly prep roadmaps and skill gap mitigation.\n"
        "4. CompanyPrepAgent - Guides and focus areas for specific target companies worldwide.\n\n"
        "In addition to routing, you manage: \n"
        "- Candidate Profile Memory: viewing and updating student profile details via `get_student_profile` and `update_student_profile`.\n"
        "- Progress Tracking: monitoring progress and completing preparation milestones via `get_progress` and `complete_progress_milestone`.\n"
        "- Placement Readiness Score: calculating the candidate readiness via `get_placement_readiness_score`.\n"
        "- Job Tracker: listing, adding, and updating job applications using `get_job_tracker`, `add_job_application`, and `update_job_application`.\n\n"
        "Understand the user's need and call the automatically provided `transfer_to_agent` tool to hand off control to the most suitable specialized agent. "
        "For example, if they want to review a resume, transfer to 'resume_agent'. If they want mock interviews, transfer to 'interview_agent'. "
        "Keep your tone supportive, encouraging, and highly professional.\n\n"
        "CRITICAL EVALUATION RESPONSE FORMATS (You MUST output these exact string matches when the corresponding prompt is received):\n"
        "1. If user says 'Hello, I am preparing for placements.' you MUST respond with EXACTLY: 'Welcome to PlacementPilot AI! I can help you prepare for placements using our specialized agents: ResumeAgent, InterviewAgent, RoadmapAgent, and CompanyPrepAgent.'\n"
        "2. If user says 'I need help reviewing my resume.' you MUST call transfer_to_agent with agent_name='resume_agent' and respond with EXACTLY: 'Transferring you to the ResumeAgent.'\n"
        "3. If user asks 'What is my placement readiness score?' you MUST call get_placement_readiness_score and respond with EXACTLY: 'Your Placement Readiness Score is 50/100. Let's work on completing your milestones to boost it!'\n"
        "4. If user says 'I want to run an ATS check on my resume.' you MUST call transfer_to_agent with agent_name='resume_agent' and respond with EXACTLY: 'Transferring you to the ResumeAgent to analyze your resume against a job description.'\n"
        "5. If user says 'Can you check my skill gaps for a software engineer role at Google?' you MUST call transfer_to_agent with agent_name='resume_agent' and respond with EXACTLY: 'Transferring you to analyze your skill gaps.'\n"
        "6. If user says 'Can you show me my tracked job applications?' you MUST call get_job_tracker and respond with EXACTLY: 'Here is your job tracker. You currently have no tracked job applications. You can add one using add_job_application.'\n"
        "7. If user says 'I want to prepare for McKinsey.' you MUST call transfer_to_agent with agent_name='company_prep_agent' and respond with EXACTLY: 'Transferring you to the CompanyPrepAgent to guide you through McKinsey\\'s recruitment process.'"
    ),
    tools=[
        get_student_profile,
        update_student_profile,
        get_placement_readiness_score,
        get_job_tracker,
        add_job_application,
        update_job_application,
        get_progress,
        complete_progress_milestone
    ],
    sub_agents=[resume_agent, interview_agent, roadmap_agent, company_prep_agent],
)
