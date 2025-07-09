import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random
import json
import time

# Configure the page
st.set_page_config(
    page_title="Rational Fish - Educational Math Game",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ocean theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e40af, #0369a1);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .score-card {
        background: linear-gradient(135deg, #0891b2, #0e7490);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
    }
    .function-card {
        background: linear-gradient(135deg, #f97316, #ea580c);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        border: 2px solid #fed7aa;
    }
    .level-badge {
        background: #059669;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0891b2, #0e7490);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Game Data Classes
class RationalFunction:
    def __init__(self, numerator, denominator, level, name):
        self.numerator = numerator  # list of coefficients
        self.denominator = denominator  # list of coefficients
        self.level = level
        self.name = name
        self.vertical_asymptotes = self.find_vertical_asymptotes()
        self.horizontal_asymptote = self.find_horizontal_asymptote()
        self.x_intercepts = self.find_x_intercepts()
        self.y_intercept = self.find_y_intercept()
        
    def find_vertical_asymptotes(self):
        # Find roots of denominator (simplified)
        if len(self.denominator) == 2:  # Linear: ax + b
            if self.denominator[0] != 0:
                return [-self.denominator[1] / self.denominator[0]]
        elif len(self.denominator) == 3:  # Quadratic: ax² + bx + c
            a, b, c = self.denominator
            if a != 0:
                discriminant = b**2 - 4*a*c
                if discriminant >= 0:
                    sqrt_disc = discriminant**0.5
                    return [(-b + sqrt_disc)/(2*a), (-b - sqrt_disc)/(2*a)]
        return []
    
    def find_horizontal_asymptote(self):
        num_degree = len(self.numerator) - 1
        den_degree = len(self.denominator) - 1
        
        if num_degree < den_degree:
            return 0
        elif num_degree == den_degree:
            return self.numerator[0] / self.denominator[0]
        else:
            return None  # No horizontal asymptote
    
    def find_x_intercepts(self):
        # Find roots of numerator (simplified)
        if len(self.numerator) == 2:  # Linear
            if self.numerator[0] != 0:
                return [-self.numerator[1] / self.numerator[0]]
        return []
    
    def find_y_intercept(self):
        # f(0) if defined
        if self.denominator[-1] != 0:
            return self.numerator[-1] / self.denominator[-1]
        return None
    
    def evaluate(self, x):
        """Evaluate the rational function at x"""
        if isinstance(x, (list, np.ndarray)):
            return [self.evaluate(xi) for xi in x]
        
        num_val = sum(coef * (x ** (len(self.numerator) - 1 - i)) for i, coef in enumerate(self.numerator))
        den_val = sum(coef * (x ** (len(self.denominator) - 1 - i)) for i, coef in enumerate(self.denominator))
        
        if abs(den_val) < 1e-10:
            return np.inf if den_val > 0 else -np.inf
        return num_val / den_val
    
    def format_polynomial(self, coeffs):
        """Format polynomial coefficients as a string"""
        if not coeffs:
            return "0"
        
        terms = []
        degree = len(coeffs) - 1
        
        for i, coef in enumerate(coeffs):
            if coef == 0:
                continue
                
            power = degree - i
            
            if power == 0:
                terms.append(str(int(coef)) if coef == int(coef) else str(coef))
            elif power == 1:
                if coef == 1:
                    terms.append("x")
                elif coef == -1:
                    terms.append("-x")
                else:
                    terms.append(f"{int(coef) if coef == int(coef) else coef}x")
            else:
                if coef == 1:
                    terms.append(f"x^{power}")
                elif coef == -1:
                    terms.append(f"-x^{power}")
                else:
                    terms.append(f"{int(coef) if coef == int(coef) else coef}x^{power}")
        
        if not terms:
            return "0"
        
        result = terms[0]
        for term in terms[1:]:
            if term.startswith('-'):
                result += f" - {term[1:]}"
            else:
                result += f" + {term}"
        
        return result
    
    def get_equation(self):
        num_str = self.format_polynomial(self.numerator)
        den_str = self.format_polynomial(self.denominator)
        return f"({num_str}) / ({den_str})"

class Question:
    def __init__(self, function, q_type, question_text, options, correct_answer, explanation, points):
        self.function = function
        self.type = q_type
        self.question_text = question_text
        self.options = options
        self.correct_answer = correct_answer
        self.explanation = explanation
        self.points = points

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'player_name': '',
        'current_level': 1,
        'score': 0,
        'lives': 5,
        'functions_caught': [],
        'current_function': None,
        'current_questions': [],
        'question_index': 0,
        'game_started': False,
        'show_feedback': False,
        'feedback_data': {},
        'leaderboard': []
    }

# Game Functions
def create_sample_functions():
    """Create sample rational functions for different levels"""
    functions = {
        1: [
            RationalFunction([1], [1, 0], 1, "f(x) = 1/x"),
            RationalFunction([2], [1, -1], 1, "f(x) = 2/(x-1)"),
            RationalFunction([1, 0], [1, -2], 1, "f(x) = x/(x-2)"),
            RationalFunction([3], [1, 1], 1, "f(x) = 3/(x+1)")
        ],
        2: [
            RationalFunction([2, 0], [1, -1], 2, "f(x) = 2x/(x-1)"),
            RationalFunction([1, -1], [1, 0, -4], 2, "f(x) = (x-1)/(x²-4)"),
            RationalFunction([1, 0, 1], [1, 0], 2, "f(x) = (x²+1)/x")
        ]
    }
    return functions

def create_questions(function):
    """Create questions for a rational function"""
    questions = []
    
    # Vertical asymptote question
    if function.vertical_asymptotes:
        va = function.vertical_asymptotes[0]
        if len(function.vertical_asymptotes) == 1:
            questions.append(Question(
                function, "vertical_asymptote",
                f"What is the vertical asymptote of {function.name}?",
                [f"x = {va}", f"x = {va+1}", f"y = {va}", "No vertical asymptote"],
                f"x = {va}",
                f"The vertical asymptote occurs where the denominator equals zero.",
                100
            ))
        else:
            va1, va2 = sorted(function.vertical_asymptotes)
            questions.append(Question(
                function, "vertical_asymptote",
                f"What are the vertical asymptotes of {function.name}?",
                [f"x = {va1} and x = {va2}", f"x = {va1}", f"x = {va2}", "No vertical asymptotes"],
                f"x = {va1} and x = {va2}",
                f"The vertical asymptotes occur where the denominator equals zero.",
                150
            ))
    
    # Horizontal asymptote question
    if function.horizontal_asymptote is not None:
        ha = function.horizontal_asymptote
        questions.append(Question(
            function, "horizontal_asymptote",
            f"What is the horizontal asymptote of {function.name}?",
            [f"y = {ha}", f"y = {ha+1}", f"y = 0", "No horizontal asymptote"],
            f"y = {ha}",
            f"Compare the degrees of numerator and denominator to find the horizontal asymptote.",
            100
        ))
    
    # X-intercept question
    if function.x_intercepts:
        xi = function.x_intercepts[0]
        questions.append(Question(
            function, "x_intercept",
            f"What is the x-intercept of {function.name}?",
            [f"x = {xi}", f"x = {xi+1}", f"x = 0", "No x-intercept"],
            f"x = {xi}",
            f"X-intercepts occur where the numerator equals zero.",
            100
        ))
    
    return questions

def plot_rational_function(function):
    """Create a plot of the rational function"""
    if not function:
        return None
    
    # Generate x values, avoiding vertical asymptotes
    x_vals = []
    y_vals = []
    
    # Create multiple segments to handle asymptotes
    x_ranges = [(-10, -5), (-4.9, -0.1), (0.1, 4.9), (5, 10)]
    
    for x_start, x_end in x_ranges:
        x_segment = np.linspace(x_start, x_end, 100)
        y_segment = []
        
        for x in x_segment:
            try:
                y = function.evaluate(x)
                if abs(y) < 100:  # Limit y values for better visualization
                    y_segment.append(y)
                else:
                    y_segment.append(None)
            except:
                y_segment.append(None)
        
        x_vals.extend(x_segment)
        y_vals.extend(y_segment)
    
    # Create the plot
    fig = go.Figure()
    
    # Add the function curve
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode='lines',
        name=function.name,
        line=dict(color='#0891b2', width=3)
    ))
    
    # Add vertical asymptotes
    for va in function.vertical_asymptotes:
        if -10 <= va <= 10:
            fig.add_vline(x=va, line_dash="dash", line_color="red", 
                         annotation_text=f"x = {va}")
    
    # Add horizontal asymptote
    if function.horizontal_asymptote is not None:
        fig.add_hline(y=function.horizontal_asymptote, line_dash="dash", 
                     line_color="green", 
                     annotation_text=f"y = {function.horizontal_asymptote}")
    
    # Add intercepts
    if function.y_intercept is not None and abs(function.y_intercept) < 100:
        fig.add_trace(go.Scatter(
            x=[0], y=[function.y_intercept],
            mode='markers',
            name='Y-intercept',
            marker=dict(color='blue', size=8)
        ))
    
    for xi in function.x_intercepts:
        if -10 <= xi <= 10:
            fig.add_trace(go.Scatter(
                x=[xi], y=[0],
                mode='markers',
                name='X-intercept',
                marker=dict(color='orange', size=8)
            ))
    
    fig.update_layout(
        title=f"Graph of {function.name}",
        xaxis_title="x",
        yaxis_title="y",
        xaxis=dict(range=[-10, 10], gridcolor='lightgray'),
        yaxis=dict(range=[-10, 10], gridcolor='lightgray'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=True
    )
    
    return fig

# Main App Layout
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🐟 Rational Fish - Educational Math Game</h1>
        <p>Catch rational functions and master their properties!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for game status
    with st.sidebar:
        st.markdown("### 🎮 Game Status")
        
        if not st.session_state.game_state['game_started']:
            st.markdown("### Welcome! Enter your name to start:")
            player_name = st.text_input("Player Name:", key="player_name_input")
            if st.button("Start Game") and player_name:
                st.session_state.game_state['player_name'] = player_name
                st.session_state.game_state['game_started'] = True
                st.rerun()
        else:
            # Game HUD
            st.markdown(f"**Player:** {st.session_state.game_state['player_name']}")
            st.markdown(f"""
            <div class="score-card">
                <h3>Score: {st.session_state.game_state['score']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="level-badge">
                Level {st.session_state.game_state['current_level']}
            </div>
            """, unsafe_allow_html=True)
            
            lives_display = "❤️ " * st.session_state.game_state['lives']
            st.markdown(f"**Lives:** {lives_display}")
            
            functions_caught = len(st.session_state.game_state['functions_caught'])
            st.markdown(f"**Functions Caught:** {functions_caught}")
            
            if st.button("🏆 View Leaderboard"):
                show_leaderboard()
            
            if st.button("🔄 New Game"):
                reset_game()
    
    if not st.session_state.game_state['game_started']:
        st.markdown("""
        ### How to Play:
        1. **Enter your name** in the sidebar to start
        2. **Choose a function** to catch from the available options
        3. **Answer questions** about the function's properties
        4. **Earn points** for correct answers
        5. **Level up** by completing all functions in a level
        
        ### What You'll Learn:
        - Vertical and horizontal asymptotes
        - X and Y intercepts
        - Function behavior and graphing
        - Rational function properties
        """)
        return
    
    # Main game area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🎣 Fishing Area - Choose a Function to Catch")
        
        # Get available functions for current level
        all_functions = create_sample_functions()
        available_functions = [f for f in all_functions.get(st.session_state.game_state['current_level'], []) 
                             if f.name not in st.session_state.game_state['functions_caught']]
        
        if not available_functions:
            st.success("🎉 Level Complete! All functions caught!")
            if st.button("Advance to Next Level"):
                advance_level()
        else:
            for i, function in enumerate(available_functions):
                st.markdown(f"""
                <div class="function-card">
                    <h4>{function.name}</h4>
                    <p>Level {function.level} Function</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Catch {function.name}", key=f"catch_{i}"):
                    catch_function(function)
    
    with col2:
        st.markdown("### 📊 Function Analysis")
        
        if st.session_state.game_state['current_function']:
            # Show current function graph
            function = st.session_state.game_state['current_function']
            st.markdown(f"**Current Function:** {function.name}")
            
            # Plot the function
            fig = plot_rational_function(function)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Show function properties
            st.markdown("**Function Properties:**")
            if function.vertical_asymptotes:
                vas = ", ".join([f"x = {va}" for va in function.vertical_asymptotes])
                st.markdown(f"- Vertical Asymptotes: {vas}")
            if function.horizontal_asymptote is not None:
                st.markdown(f"- Horizontal Asymptote: y = {function.horizontal_asymptote}")
            if function.x_intercepts:
                xis = ", ".join([f"x = {xi}" for xi in function.x_intercepts])
                st.markdown(f"- X-intercepts: {xis}")
            if function.y_intercept is not None:
                st.markdown(f"- Y-intercept: y = {function.y_intercept}")
        else:
            st.info("Catch a function to see its graph and properties!")
    
    # Question Panel
    if (st.session_state.game_state['current_function'] and 
        st.session_state.game_state['current_questions']):
        
        st.markdown("---")
        st.markdown("### 🤔 Answer the Question")
        
        questions = st.session_state.game_state['current_questions']
        q_index = st.session_state.game_state['question_index']
        
        if q_index < len(questions):
            question = questions[q_index]
            
            st.markdown(f"**Question {q_index + 1} of {len(questions)}:**")
            st.markdown(f"**{question.question_text}**")
            
            # Multiple choice options
            answer = st.radio("Choose your answer:", question.options, key=f"q_{q_index}")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Submit Answer"):
                    submit_answer(question, answer)
            with col2:
                if st.button("Get Hint"):
                    show_hint(question)
            with col3:
                if st.button("Skip Question"):
                    next_question()

def catch_function(function):
    """Handle catching a function"""
    st.session_state.game_state['current_function'] = function
    st.session_state.game_state['current_questions'] = create_questions(function)
    st.session_state.game_state['question_index'] = 0
    st.session_state.game_state['functions_caught'].append(function.name)
    
    st.success(f"🎣 Caught {function.name}! Answer questions to earn points.")
    st.rerun()

def submit_answer(question, answer):
    """Handle answer submission"""
    is_correct = answer == question.correct_answer
    points = question.points if is_correct else 0
    
    if is_correct:
        st.session_state.game_state['score'] += points
        st.success(f"✅ Correct! +{points} points")
        st.info(f"**Explanation:** {question.explanation}")
    else:
        st.session_state.game_state['lives'] -= 1
        st.error(f"❌ Incorrect. The correct answer was: {question.correct_answer}")
        st.info(f"**Explanation:** {question.explanation}")
    
    if st.session_state.game_state['lives'] <= 0:
        st.error("💀 Game Over! You ran out of lives.")
        return
    
    # Auto-advance to next question after a short delay
    time.sleep(2)
    next_question()

def next_question():
    """Move to the next question"""
    st.session_state.game_state['question_index'] += 1
    
    if (st.session_state.game_state['question_index'] >= 
        len(st.session_state.game_state['current_questions'])):
        # Function complete
        st.session_state.game_state['current_function'] = None
        st.session_state.game_state['current_questions'] = []
        st.session_state.game_state['question_index'] = 0
        st.success("🌟 Function complete! Catch another function to continue.")
    
    st.rerun()

def show_hint(question):
    """Show a hint for the current question"""
    hints = {
        "vertical_asymptote": "Look for values that make the denominator equal to zero.",
        "horizontal_asymptote": "Compare the degrees of the numerator and denominator.",
        "x_intercept": "Find where the numerator equals zero (but denominator doesn't).",
        "y_intercept": "Substitute x = 0 into the function."
    }
    
    hint = hints.get(question.type, "Think about the function's properties.")
    st.info(f"💡 **Hint:** {hint}")

def advance_level():
    """Advance to the next level"""
    st.session_state.game_state['current_level'] += 1
    st.session_state.game_state['functions_caught'] = []
    st.session_state.game_state['current_function'] = None
    st.session_state.game_state['current_questions'] = []
    st.success(f"🎉 Welcome to Level {st.session_state.game_state['current_level']}!")
    st.rerun()

def show_leaderboard():
    """Display the leaderboard"""
    st.markdown("### 🏆 Leaderboard")
    
    # Add current player to leaderboard
    player_data = {
        'name': st.session_state.game_state['player_name'],
        'score': st.session_state.game_state['score'],
        'level': st.session_state.game_state['current_level']
    }
    
    # Simple leaderboard (in real app, this would be persistent)
    leaderboard = [player_data]
    df = pd.DataFrame(leaderboard)
    df = df.sort_values('score', ascending=False)
    
    st.dataframe(df, use_container_width=True)

def reset_game():
    """Reset the game"""
    st.session_state.game_state = {
        'player_name': '',
        'current_level': 1,
        'score': 0,
        'lives': 5,
        'functions_caught': [],
        'current_function': None,
        'current_questions': [],
        'question_index': 0,
        'game_started': False,
        'show_feedback': False,
        'feedback_data': {},
        'leaderboard': []
    }
    st.rerun()

if __name__ == "__main__":
    main()