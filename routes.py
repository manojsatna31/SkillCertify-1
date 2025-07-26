from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
import logging
import time
from core.exam_manager import ExamManager
from core.question_bank_loader import QuestionBankLoader

bp = Blueprint('main', __name__)
qb_loader = QuestionBankLoader()
exam_manager = ExamManager()


@bp.route('/')
def home():
    exam_manager.clear_exam_session(session)
    topics = qb_loader.get_topics()
    return render_template('home.html', topics=topics)


@bp.route('/topic/<topic_id>')
def set_selection(topic_id):
    topic_data = qb_loader.load_topic(topic_id)
    if not topic_data:
        return redirect(url_for('main.home'))

    return render_template('set_selection.html', topic=topic_data)


@bp.route('/start-exam/<topic_id>/<set_id>')
def start_exam(topic_id, set_id):
    if exam_manager.start_exam(session, topic_id, set_id):
        return redirect(url_for('main.start_exam_confirm',topic_id=topic_id,set_id=set_id ))
        # return redirect(url_for('main.take_exam'))
    return redirect(url_for('main.set_selection', topic_id=topic_id))

@bp.route("/start-exam-confirm/<topic_id>/<set_id>")
def start_exam_confirm(topic_id, set_id):
    exam = exam_manager._get_exam(session)
    if not exam:
        return redirect(url_for('main.home'))

    # question = exam_manager.get_current_question(session)

    return render_template(
        'Exam-Start-Confirmation-Screen.html',
        total_questions=len(exam['questions']),
        set_name=exam.get('set_name', 'test exam'),  # ✅ was session.exam.set_name
        time_limit=exam.get('time_limit', 5400),
        passing_score="75",
    )

@bp.route('/take-exam')
def take_exam():
    exam = exam_manager._get_exam(session)
    if not exam:
        return redirect(url_for('main.home'))

    question = exam_manager.get_current_question(session)

    return render_template(
        'exam.html',
        question=question,
        question_index=exam['current_index'],
        total_questions=len(exam['questions']),
        set_name=exam.get('set_name','test exam'),  # ✅ was session.exam.set_name
        answers=exam.get('answers', {}),
        review=exam.get('review', []),
        time_limit=exam.get('time_limit', 5400),
        start_time=int(exam.get('start_time', time.time()))  # ✅ Required
    )


@bp.route('/submit-answer', methods=['POST'])
def submit_answer():
    if not exam_manager._get_exam(session):
        return jsonify({'success': False}), 401

    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        question_id = data.get('question_id')
        answer_index = data.get('answer_index')
        if question_id is None or answer_index is None:
            return jsonify({
                'success': False,
                'error': 'Missing question_id or answer_index'
            }), 400

        success = exam_manager.submit_answer(session, question_id, answer_index)
        return jsonify({'success': success})

    except Exception as e:
        logging.error(f"Error in submit_answer: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@bp.route('/toggle-review', methods=['POST'])
def toggle_review():
    if not exam_manager._get_exam(session):
        return jsonify({'success': False}), 401

    try:
        data = request.json
        question_id = data.get('question_id')

        # Convert to int if possible to ensure consistent typing
        try:
            question_id = int(question_id)
        except (TypeError, ValueError):
            pass
        success = exam_manager.toggle_review(session, data.get('question_id'))

        if success:
            exam = exam_manager._get_exam(session)
            review_count = len(exam.get('review', []))
            return jsonify({
                'success': True,
                'review_count': review_count
            })
        return jsonify({'success': False})
    except Exception as e:
        logging.error(f"Error in toggle_review: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@bp.route('/next-review')
def next_review():
    if not exam_manager._get_exam(session):
        return redirect(url_for('main.home'))

    if exam_manager.next_review(session):
        return redirect(url_for('main.take_exam'))

    # If no review questions, stay on current question
    return redirect(url_for('main.take_exam'))


@bp.route('/prev-review')
def prev_review():
    if not exam_manager._get_exam(session):
        return redirect(url_for('main.home'))

    if exam_manager.prev_review(session):
        return redirect(url_for('main.take_exam'))

    # If no review questions, stay on current question
    return redirect(url_for('main.take_exam'))

@bp.route('/next-question')
def next_question():
    if not exam_manager._get_exam(session):
        return jsonify({'success': False}), 401

    if exam_manager.next_question(session):
        return redirect(url_for('main.take_exam'))

    return redirect(url_for('main.finish_exam'))


@bp.route('/prev-question')
def prev_question():
    exam_manager.prev_question(session)
    return redirect(url_for('main.take_exam'))


@bp.route('/question-explanation')
def question_explanation():
    """
    Securely return explanation and correct answer for post-exam question.
    exam['answers'][question_id] = {
            'selected': answer_index,
            'timestamp': datetime.now(timezone.utc)
        }
    """
    exam = exam_manager._get_exam(session)
    if not exam:
        return jsonify({'error': 'Report not available'}), 404

    report_data = exam['exam_report']
    topic_id = report_data.get('topic_id')
    set_id = report_data.get('set_id')

    try:
        question_index = int(request.args.get('question_index'))
        if question_index < 0:
            raise ValueError("Index must be positive")

        # Get question from report (safe text only)
        question_report = report_data['report']['questions'][question_index]
        question_id = question_report['question_id']

        # Load full set with answer key
        full_set = qb_loader.load_full_set(topic_id, set_id)

        # Locate original question in full set
        original_question = next((q for q in full_set['questions'] if q['id'] == question_id), None)
        if not original_question:
            return jsonify({'error': 'Not found'}), 404

        # Handle missing selected answer safely
        answer_info = exam.get('answers', {}).get(original_question.get('id'), {})
        selected_answer = answer_info.get('selected', -1)

        return jsonify({
            'question_text': question_report['question_text'],
            'options': question_report['options'],
            'correct_answer': original_question.get('correct_answer_index'),
            'selected_answer' : selected_answer,
            'explanation': original_question.get('explanation', 'No explanation available')
        })
    except Exception as e:
        logging.exception("Failed to fetch explanation")
        return jsonify({'error': 'Unexpected error occurred'}), 500


@bp.route('/admin')
def admin_dashboard():
    topics = qb_loader.get_topics()
    return render_template('admin/dashboard.html', topics=topics)


@bp.route('/admin/topic/<topic_id>')
def admin_topic(topic_id):
    topic_data = qb_loader.load_topic(topic_id)
    if not topic_data:
        return redirect(url_for('main.admin_dashboard'))
    return render_template('admin/topic.html', topic=topic_data)


@bp.route('/admin/edit-question/<question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    # In real implementation, would fetch question from DB
    return render_template('admin/edit_question.html', question_id=question_id)


@bp.route('/finish-exam')
def finish_exam():
    exam = exam_manager._get_exam(session)
    report = exam_manager.finish_exam(session)
    if not report:
        return redirect(url_for('main.home'))

    exam['exam_report'] = {
        'report': report,
        'topic_id': exam['topic_id'],
        'set_id': exam['set_id']
    }

    # exam_manager.clear_exam_session(session)

    print("session keys at /finish-exam:", list(session.keys()))

    return render_template('post_exam.html', report=report)


@bp.route('/exam-report')
def exam_report():
    print("session keys at /exam-report:", list(session.keys()))
    exam = exam_manager._get_exam(session)
    if 'exam_report' not in exam:
        return redirect(url_for('main.home'))
    report_data = exam['exam_report']
    logging.info(f"report_data={report_data}")
    # exam_manager.clear_exam_session(session)
    return render_template(
        'report.html',
        report=report_data['report'],
        topic=report_data['topic_id'],
        set_name=report_data['set_id']
    )
