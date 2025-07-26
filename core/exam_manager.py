import datetime
import logging
import time
from datetime import datetime, timezone
from core.question_bank_loader import QuestionBankLoader
from uuid import uuid4

logger = logging.getLogger(__name__)
qb_loader = QuestionBankLoader()


class ExamManager:
    def __init__(self):
        self.live_sessions = {}

    def start_exam(self, session, topic_id, set_id):
        """Start exam with sanitized questions (no answers in session)"""
        try:
            exam_set = qb_loader.load_set(topic_id, set_id)
            if not exam_set:
                return False

            exam_id = str(uuid4())

            # session['exam'] = {
            self.live_sessions[exam_id] = {
                'topic_id': topic_id,
                'set_name':exam_set['name'],
                'set_id': set_id,
                'start_time': time.time(),
                'current_index': 0,
                'answers': {},
                'review': [],  # Changed to 'review' to match other methods
                'questions': exam_set['questions'],  # Add questions to session
                'time_limit': 90 * 60  # 90 minutes in seconds
            }
            session['exam_id'] = exam_id
        except Exception as e:
            logger.error(f"Error starting exam: {e}")
            return False
        return True

    def _get_exam(self, session):
        exam_id = session.get('exam_id')
        return self.live_sessions.get(exam_id)

    def get_current_question(self, session):
        """Get current question data"""
        # Return current question in session
        exam = self._get_exam(session)
        if not exam:
            return None
        return exam['questions'][exam['current_index']]

    def submit_answer(self, session, question_id, answer_index):
        """Record user's answer"""
        exam = self._get_exam(session)

        exam['answers'][question_id] = {
            'selected': answer_index,
            'timestamp': datetime.now(timezone.utc)
        }
        session.modified = True
        return True

    def toggle_review(self, session, question_id):
        """Toggle review status for a question"""
        # Mark or unmark a question for review
        exam = self._get_exam(session)

        if not exam:
            return False


        # Ensure consistent typing
        if isinstance(question_id, str) and question_id.isdigit():
            question_id = int(question_id)

        # Convert existing review IDs to same type as incoming question_id
        review_ids = [int(qid) if isinstance(qid, str) and qid.isdigit() else qid
                      for qid in exam['review']]

        if question_id in review_ids:
            exam['review'] = [qid for qid in exam['review']
                              if (int(qid) if isinstance(qid, str) and qid.isdigit() else qid) != question_id]
        else:
            exam['review'].append(question_id)

        session.modified = True
        return True

    def next_question(self, session):
        """Move to next question"""
        # Move to next question
        exam = self._get_exam(session)

        if exam['current_index'] >= len(exam['questions']) - 1:
            return False
        exam['current_index'] += 1
        session.modified = True
        return True

    def prev_question(self, session):
        """Move to previous question"""
        exam = self._get_exam(session)
        if exam['current_index'] <= 0:
            return False
        exam['current_index'] -= 1
        session.modified = True
        return True

    def finish_exam(self, session):
        """At report time, re-load full set with answers and validate"""
        exam = self._get_exam(session)

        full_set = qb_loader.load_full_set(exam['topic_id'], exam['set_id'])
        if not full_set:
            logger.error("Cannot validate report: full set not found.")
            return None

        question_lookup = {q['id']: q for q in full_set['questions']}
        total_question = len(exam['questions'])

        report = {
            'topic_id': exam['topic_id'],
            'set_id':exam['set_id'],
            'total_questions': total_question,
            'correct_answers': 0,
            'incorrect_answers': 0,
            'score': 0,
            'questions': [],
            'domains': {},
            'time_taken': time.time() - exam['start_time']
        }

        for i, question in enumerate(exam['questions']):
            qid = question['id']
            full = question_lookup.get(qid, {})
            correct = full.get('correct_answer_index', -1)
            explanation = full.get('explanation', 'N/A')
            user_data = exam['answers'].get(qid, {})
            selected = user_data.get('selected', '-1')
            is_correct = (selected == correct)

            domain = question.get('domain', 'General')
            report['correct_answers'] += int(is_correct)
            report['questions'].append({
                'index': i,
                'question_id': qid,
                'question_text': question['question_text'],
                'options': question['options'],
                'correct_answer': correct,
                'user_answer': selected,
                'is_correct': is_correct,
                'explanation': explanation,
                'marked_review': qid in exam['review']
            })

            if domain not in report['domains']:
                report['domains'][domain] = {'total': 0, 'correct': 0}
            report['domains'][domain]['total'] += 1
            report['domains'][domain]['correct'] += int(is_correct)

        for domain, stats in report['domains'].items():
            stats['percentage'] = round((stats['correct'] / stats['total']) * 100, 2)

        report['score'] = int((report['correct_answers'] / report['total_questions']) * 100)
        report['incorrect_answers'] =  int(report['total_questions']) - int(report['correct_answers'])
        report['topic'] = full_set['name']

        logger.info(f'report->{report}')

        return report

    def clear_exam_session(self, session):
        exam_id = session.pop('exam_id', None)
        if exam_id:
            self.live_sessions.pop(exam_id,None)
        session.modified = True

    def next_review(self, session):
        """Move to next review question"""
        exam = self._get_exam(session)
        if not exam or not exam['review']:
            return False

        # Get indices of all review questions
        review_indices = []
        for i, q in enumerate(exam['questions']):
            if q['id'] in exam['review']:
                review_indices.append(i)

        if not review_indices:
            return False

        # Find next review index after current position
        current_idx = exam['current_index']
        next_idx = None
        for idx in review_indices:
            if idx > current_idx:
                next_idx = idx
                break

        # If none found, wrap to first review question
        if next_idx is None:
            next_idx = review_indices[0]

        exam['current_index'] = next_idx
        session.modified = True
        return True

    def prev_review(self, session):
        """Move to previous review question"""
        exam = self._get_exam(session)
        if not exam or not exam['review']:
            return False

        # Get indices of all review questions
        review_indices = []
        for i, q in enumerate(exam['questions']):
            if q['id'] in exam['review']:
                review_indices.append(i)

        if not review_indices:
            return False

        # Find previous review index before current position
        current_idx = exam['current_index']
        prev_idx = None
        for idx in reversed(review_indices):
            if idx < current_idx:
                prev_idx = idx
                break

        # If none found, wrap to last review question
        if prev_idx is None:
            prev_idx = review_indices[-1]

        exam['current_index'] = prev_idx
        session.modified = True
        return True


