from flask import Flask, request, jsonify, render_template
import numpy as np

# CareerMatcher Class (remains the same)
class CareerMatcher:
    def __init__(self, career_data):
        self.data = career_data
        self.weights = self.data["assessment_weights"]

    def calculate_similarity(self, text1, text2):
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0

    def analyze_personality_match(self, user_traits, career_traits):
        user_trait_set = set(user_traits)
        career_trait_set = set(career_traits)
        direct_match_score = len(user_trait_set.intersection(career_trait_set)) / len(career_trait_set) if career_trait_set else 0
        return direct_match_score

    def analyze_skills_match(self, user_skills, required_skills):
        total_score = 0
        for user_skill in user_skills:
            max_skill_score = max(self.calculate_similarity(user_skill, req_skill) for req_skill in required_skills) if required_skills else 0
            total_score += max_skill_score
        return total_score / len(required_skills) if required_skills else 0

    def match_career_path(self, user_profile):
        matches = []
        for field, careers in self.data["career_mappings"].items():
            personality_score = self.analyze_personality_match(user_profile.get("traits", []), careers["matching_traits"])
            avg_skills_score = np.mean([self.analyze_skills_match(user_profile.get("skills", []), career["skills_required"]) for career in careers["careers"]])
            final_score = personality_score * self.weights["personality_match"] + avg_skills_score * self.weights["skills_match"]
            matches.append({"field": field, "overall_score": final_score, "careers": careers["careers"]})
        matches.sort(key=lambda x: x["overall_score"], reverse=True)
        return matches

# CareerCounselingChatbot Class (remains the same)
class CareerCounselingChatbot:
    def __init__(self, career_data):
        self.matcher = CareerMatcher(career_data)
        self.data = career_data
        self.user_profile = {"traits": [], "skills": [], "preferences": [], "experience": []}
        self.conversation_state = "START"
        self.current_question_index = 0

        self.conversation_flow = {
            "START": {
                "questions": ["Hi! I'm your career counseling assistant. Would you like to start your career assessment?"],
                "next_state": "TRAITS",
                "process_func": self._process_start
            },
            "TRAITS": {
                "questions": [
                    "Great! Let's start by understanding your personality traits. How would you describe your personality? (e.g., analytical, practical, social)"
                ],
                "next_state": "SKILLS",
                "process_func": self._process_traits
            },
            "SKILLS": {
                "questions": [
                    "Now, let's talk about your skills. What skills do you have? (e.g., programming, communication)"
                ],
                "next_state": "MATCH",
                "process_func": self._process_skills
            },
            "MATCH": {
                "questions": [],
                "next_state": None,
                "process_func": self._process_match
            },
        }

    def _process_start(self, user_input):
        if "yes" in user_input.lower():
            return "Let's begin with understanding your personality traits.", True
        return "Let me know when you'd like to start.", False

    def _process_traits(self, user_input):
        # Assume user inputs traits as a comma-separated string
        traits = [trait.strip().lower() for trait in user_input.split(",")]
        self.user_profile["traits"] = traits
        return "Thanks for sharing your traits.", True

    def _process_skills(self, user_input):
        # Assume user inputs skills as a comma-separated string
        skills = [skill.strip().lower() for skill in user_input.split(",")]
        self.user_profile["skills"] = skills
        return "Thanks for sharing your skills.", True

    def _process_match(self, user_input):
        # This could be a placeholder for now, where the chatbot processes and gives results
        matches = self.matcher.match_career_path(self.user_profile)
        if matches:
            top_match = matches[0]  # Getting the best match
            return f"I think you may be interested in a career in {top_match['field']}, such as {top_match['careers'][0]['title']}.", True
        return "Sorry, I couldn't find a good match for your profile.", True

    def get_next_question(self):
        current_state = self.conversation_flow[self.conversation_state]
        if self.current_question_index < len(current_state["questions"]):
            return current_state["questions"][self.current_question_index]
        return ""

    def process_input(self, user_input):
        current_state = self.conversation_flow[self.conversation_state]
        response, proceed = current_state["process_func"](user_input)
        if proceed:
            self.current_question_index += 1
            if self.current_question_index >= len(current_state["questions"]):
                self.conversation_state = current_state["next_state"]
                self.current_question_index = 0
            next_question = self.get_next_question()
            return f"{response}\n\n{next_question}" if next_question else response
        return response

# Flask App
app = Flask(__name__)

# Initialize the chatbot with sample career data
career_counseling_data = {
    "assessment_weights": {
        "personality_match": 0.5,
        "skills_match": 0.5,
    },
    "career_mappings": {
        "Technology": {
            "matching_traits": ["analytical", "practical"],
            "careers": [{"title": "Software Engineer", "skills_required": ["programming", "data analysis"]}]
        },
        "Business": {
            "matching_traits": ["social", "enterprising"],
            "careers": [{"title": "Business Analyst", "skills_required": ["communication", "analysis"]}]
        }
    }
}
chatbot = CareerCounselingChatbot(career_counseling_data)

@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if user_input is None:
        return jsonify({"error": "No message provided"}), 400

    response = chatbot.process_input(user_input)
    
    return jsonify({"response": response})

@app.route('/start', methods=['GET'])
def start():
    # Initialize the chatbot state
    chatbot.conversation_state = "START"
    chatbot.current_question_index = 0
    initial_question = chatbot.get_next_question()
    return jsonify({"response": initial_question})

if __name__ == '__main__':
    app.run(debug=True)
