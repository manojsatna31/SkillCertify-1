import json
import logging
import os
from config import settings

logger = logging.getLogger(__name__)


class QuestionBankLoader:
    def __init__(self):
        # Load topic metadata from manifest file
        self.manifest = self._load_manifest()
        self.loaded_topics = {}  # cache without answers
        self.answer_topics = {}  # optional cache with answers

    def _load_manifest(self):
        # Read manifest JSON file listing all topics
        try:
            with open(settings.config.QB_MANIFEST_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.critical(f"Failed to load manifest: {str(e)}")
            return []

    def get_topics(self):
        """Get topic metadata without loading question data"""
        # Return summary info for all topics
        return [{
            'topic_id': t['topic_id'],
            'title': t['title'],
            'description': t['description'],
            'icon': t['icon']
        } for t in self.manifest]

    def load_topic(self, topic_id ):
        """Lazy load topic data with exam sets (without answers)"""
        if topic_id in self.loaded_topics:
            return self.loaded_topics[topic_id]

        topic_config = next((t for t in self.manifest if t['topic_id'] == topic_id), None)
        if not topic_config:
            logger.error(f"Topic not found: {topic_id}")
            return None

        try:
            # Load question set from corresponding JSON file
            file_path = os.path.join(settings.config.QB_DATA_DIR, topic_config['filename'])
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'topic_id' not in data:
                    data['topic_id'] = topic_id  # Ensure topic_id exists

            # # Sanitize questions and add metadata - remove answers
            for exam_set in data['exam_sets']:
                for question in exam_set['questions']:
                    question['topic_id'] = topic_id
                    # Remove sensitive data
                    question.pop('correct_answer_index', None)
                    question.pop('explanation', None)
                    # Rename topic_id to set_id if needed
                    if 'topic_id' in exam_set:
                        exam_set['set_id'] = exam_set.pop('topic_id')

            self.loaded_topics[topic_id] = data
            return data
        except Exception as e:
            logger.error(f"Error loading topic {topic_id}: {str(e)}")
            return None

    def load_set(self, topic_id, set_id):
        """Load sanitized set without answers"""
        topic_data = self.load_topic(topic_id)
        if not topic_data:
            return None

        for exam_set in topic_data.get('exam_sets', []):
            if exam_set.get('set_id') == set_id and 'questions' in exam_set:
                return exam_set

        return None

    def load_full_set(self, topic_id, set_id):
        """load full version with answers for report validation"""
        topic_config = next((t for t in self.manifest if t['topic_id'] == topic_id), None)
        if not topic_config:
            logger.error(f"Topic not found for full load: {topic_id}")
            return None

        try:
            file_path = os.path.join(settings.config.QB_DATA_DIR, topic_config['filename'])
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for exam_set in data.get('exam_sets', []):
                if exam_set.get('topic_id') == set_id or exam_set.get('set_id') == set_id:
                    return exam_set
        except Exception as e:
            logger.error(f"Failed to load full set for {topic_id}/{set_id}: {str(e)}")
            return None