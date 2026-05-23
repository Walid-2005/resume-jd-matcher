import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import AnalysisHistory, AnalysisFeedback
from .services.resume_parser import ResumeParser
from .services.matcher import JobMatcher
from .services.report_generator import generate_pdf, generate_docx, generate_html
from .services.job_fetcher import fetch_job_description, JobFetchError
from .services.job_recommender import get_job_recommendations


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Register a new user."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username, email, and password are required'
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Username already exists'
            }, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Email already exists'
            }, status=400)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """Login a user."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Logout a user."""
    logout(request)
    return JsonResponse({
        'status': 'success',
        'message': 'Logout successful'
    })


@require_http_methods(["GET"])
def check_auth(request):
    """Check if user is authenticated."""
    if request.user.is_authenticated:
        return JsonResponse({
            'status': 'success',
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    else:
        return JsonResponse({
            'status': 'success',
            'authenticated': False
        })


@csrf_exempt
@require_http_methods(["POST"])
def analyze_resume(request):
    """Analyze resume and match with job description."""
    try:
        if 'resume_file' not in request.FILES:
            response = JsonResponse({
                'status': 'error',
                'message': 'Resume file is required'
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        resume_file = request.FILES['resume_file']
        job_description = request.POST.get('job_description', '')
        
        if not job_description:
            response = JsonResponse({
                'status': 'error',
                'message': 'Job description is required'
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        # Validate file type
        file_name = resume_file.name.lower()
        if not (file_name.endswith('.pdf') or file_name.endswith('.docx') or file_name.endswith('.doc')):
            response = JsonResponse({
                'status': 'error',
                'message': 'Unsupported file format. Please upload a PDF or DOCX file.'
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        # Parse resume
        parser = ResumeParser()
        resume_text = parser.extract_text(resume_file)
        
        # Debug logging
        print(f"Resume text length: {len(resume_text) if resume_text else 0}")
        print(f"Resume text preview: {resume_text[:200] if resume_text else 'None'}")
        print(f"Job description length: {len(job_description)}")
        print(f"Job description preview: {job_description[:200]}")
        
        if not resume_text or len(resume_text.strip()) < 50:
            response = JsonResponse({
                'status': 'error',
                'message': 'Could not extract sufficient text from the resume. Please ensure the file is not corrupted and contains readable text.'
            }, status=400)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        # Match with job description
        matcher = JobMatcher()
        analysis = matcher.generate_full_analysis(resume_text, job_description)
        
        # Debug logging for analysis
        print(f"Analysis match score: {analysis.get('matchScore', 0)}")
        print(f"Found skills count: {len(analysis.get('foundSkills', []))}")
        print(f"Missing skills count: {len(analysis.get('missingSkills', []))}")

        # Save to history if user is authenticated
        history_id = None
        if request.user.is_authenticated:
            record = AnalysisHistory.objects.create(
                user=request.user,
                match_score=analysis['matchScore'],
                found_skills=analysis['foundSkills'],
                missing_skills=analysis['missingSkills'],
                strengths=analysis['strengths'],
                weaknesses=analysis['weaknesses'],
                recommendations=analysis['recommendations'],
                ai_insight=analysis['aiInsight'],
                job_description=job_description[:2000],
            )
            history_id = record.id

        response = JsonResponse({
            'status': 'success',
            'historyId': history_id,
            **analysis
        })
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    except ValueError as e:
        # Handle validation errors
        response = JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        # Handle unexpected errors
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in analyze_resume: {error_details}")  # For debugging

        response = JsonResponse({
            'status': 'error',
            'message': f'An error occurred while processing your resume: {str(e)}'
        }, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


@csrf_exempt
@require_http_methods(["GET"])
def analysis_history_list(request):
    """Return the authenticated user's analysis history."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    records = AnalysisHistory.objects.filter(user=request.user)[:50]
    response = JsonResponse({
        'status': 'success',
        'history': [r.to_dict() for r in records],
    })
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@require_http_methods(["GET"])
def analysis_history_detail(request, history_id):
    """Return a single analysis record."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    try:
        record = AnalysisHistory.objects.get(id=history_id, user=request.user)
    except AnalysisHistory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)

    response = JsonResponse({'status': 'success', **record.to_dict()})
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@require_http_methods(["DELETE"])
def analysis_history_delete(request, history_id):
    """Delete a single analysis record."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    try:
        record = AnalysisHistory.objects.get(id=history_id, user=request.user)
    except AnalysisHistory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)

    record.delete()
    response = JsonResponse({'status': 'success', 'message': 'Record deleted'})
    response['Access-Control-Allow-Origin'] = '*'
    return response


_VALID_SCORE_RATINGS = {'too_high', 'accurate', 'too_low'}


def _client_ip_hash(request) -> str:
    """Hash the remote IP for dedup without storing raw IPs."""
    import hashlib
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
        or request.META.get('REMOTE_ADDR', '')
    return hashlib.sha256(ip.encode()).hexdigest()[:32] if ip else ''


@csrf_exempt
@require_http_methods(["POST"])
def submit_feedback(request):
    """Accept user feedback on a completed analysis.

    Body (JSON):
      historyId:     int | null   — links to AnalysisHistory when available
      scoreRating:   'too_high' | 'accurate' | 'too_low' | null
      usefulness:    1–5 | null   — overall usefulness rating
      comment:       string       — optional freeform feedback
      snapshot:      object       — optional client-side copy of the result
                                     (matchScore, foundSkills, missingSkills,
                                      strengths, weaknesses, jdExcerpt)

    Anonymous users are accepted — both `user` and `analysis` can be null,
    and the snapshot field keeps the row self-contained for offline analysis.
    """
    try:
        data = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    history_id    = data.get('historyId')
    score_rating  = data.get('scoreRating')
    usefulness    = data.get('usefulness')
    comment       = (data.get('comment') or '').strip()[:2000]
    snapshot      = data.get('snapshot') or {}

    # ── Validation ────────────────────────────────────────────────────────
    if score_rating is not None and score_rating not in _VALID_SCORE_RATINGS:
        return JsonResponse({
            'status': 'error',
            'message': f"scoreRating must be one of {sorted(_VALID_SCORE_RATINGS)}",
        }, status=400)

    if usefulness is not None:
        try:
            usefulness = int(usefulness)
            if not 1 <= usefulness <= 5:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse({
                'status': 'error',
                'message': 'usefulness must be an integer 1–5',
            }, status=400)

    # Require at least one signal — reject completely empty submissions
    if score_rating is None and usefulness is None and not comment:
        return JsonResponse({
            'status': 'error',
            'message': 'Provide at least one of scoreRating, usefulness, or comment',
        }, status=400)

    # ── Link to history record when possible ──────────────────────────────
    analysis = None
    if history_id is not None and request.user.is_authenticated:
        try:
            analysis = AnalysisHistory.objects.get(id=history_id, user=request.user)
        except AnalysisHistory.DoesNotExist:
            analysis = None

    # ── Build snapshot fields from client payload ─────────────────────────
    match_score = snapshot.get('matchScore') if isinstance(snapshot, dict) else None
    try:
        match_score = int(match_score) if match_score is not None else None
    except (TypeError, ValueError):
        match_score = None

    jd_excerpt = ''
    if isinstance(snapshot, dict):
        jd_excerpt = (snapshot.get('jdExcerpt') or '')[:2000]
    elif analysis:
        jd_excerpt = (analysis.job_description or '')[:2000]

    # Prefer the server-side record's truth when we have it
    if analysis is not None and match_score is None:
        match_score = analysis.match_score

    # ── Create the feedback row ───────────────────────────────────────────
    feedback = AnalysisFeedback.objects.create(
        analysis     = analysis,
        user         = request.user if request.user.is_authenticated else None,
        score_rating = score_rating,
        usefulness   = usefulness,
        comment      = comment,
        match_score  = match_score,
        snapshot     = snapshot if isinstance(snapshot, dict) else {},
        jd_excerpt   = jd_excerpt,
        user_agent   = request.META.get('HTTP_USER_AGENT', '')[:255],
        ip_hash      = _client_ip_hash(request),
    )

    response = JsonResponse({
        'status':     'success',
        'message':    'Thanks for the feedback!',
        'feedbackId': feedback.id,
    })
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@require_http_methods(["POST"])
def export_report(request, fmt):
    """Export analysis results as PDF, DOCX, or HTML.

    Accepts JSON body with analysis data. If a ``historyId`` field is present
    and the user is authenticated, the saved record is used instead.
    """
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if fmt not in ('pdf', 'docx', 'html'):
        response = JsonResponse({'status': 'error', 'message': 'Unsupported format. Use pdf, docx, or html.'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        response = JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    # If a historyId is provided, load from DB (requires auth)
    history_id = data.get('historyId')
    if history_id and request.user.is_authenticated:
        try:
            record = AnalysisHistory.objects.get(id=history_id, user=request.user)
            data = record.to_dict()
        except AnalysisHistory.DoesNotExist:
            response = JsonResponse({'status': 'error', 'message': 'Record not found'}, status=404)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    try:
        if fmt == 'pdf':
            content = generate_pdf(data)
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="ResuMatch_Report.pdf"'
        elif fmt == 'docx':
            content = generate_docx(data)
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            )
            response['Content-Disposition'] = 'attachment; filename="ResuMatch_Report.docx"'
        else:  # html
            content = generate_html(data)
            response = HttpResponse(content, content_type='text/html')
            response['Content-Disposition'] = 'attachment; filename="ResuMatch_Report.html"'

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response

    except Exception as e:
        import traceback
        print(f"Error in export_report: {traceback.format_exc()}")
        response = JsonResponse({'status': 'error', 'message': f'Export failed: {str(e)}'}, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def fetch_job(request):
    """Fetch a job description from a LinkedIn or Indeed URL."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        response = JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    url = data.get('url', '').strip()
    if not url:
        response = JsonResponse({'status': 'error', 'message': 'URL is required'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    try:
        result = fetch_job_description(url)
        response = JsonResponse({'status': 'success', **result})
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except JobFetchError as e:
        response = JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        import traceback
        print(f"Error in fetch_job: {traceback.format_exc()}")
        response = JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred while fetching the job description.'
        }, status=500)
        response['Access-Control-Allow-Origin'] = '*'
        return response


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def recommend_jobs(request):
    """Return job recommendations based on resume skills."""
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        response = JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    skills = data.get('skills', [])
    experience_level = data.get('experienceLevel', 'mid')
    location = data.get('location', '')

    if not skills:
        response = JsonResponse({'status': 'error', 'message': 'No skills provided'}, status=400)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    recommendations = get_job_recommendations(
        resume_skills=skills,
        experience_level=experience_level,
        location=location,
        max_results=20,
    )

    response = JsonResponse({
        'status': 'success',
        'recommendations': recommendations,
    })
    response['Access-Control-Allow-Origin'] = '*'
    return response

