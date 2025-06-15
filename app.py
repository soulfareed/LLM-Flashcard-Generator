import streamlit as st
import os
import json
from flashcard_generator import FlashcardGenerator
from file_processor import FileProcessor
from exporter import FlashcardExporter
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="LLM Flashcard Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'generator' not in st.session_state:
    st.session_state.generator = FlashcardGenerator()

def main():
    st.title("🧠 LLM-Powered Flashcard Generator")
    st.markdown("Transform your educational content into effective flashcards using AI")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Subject selection
    subjects = [
        "General", "Biology", "Chemistry", "Physics", "Mathematics", 
        "History", "Computer Science", "Literature", "Psychology", "Economics"
    ]
    selected_subject = st.sidebar.selectbox("📚 Select Subject", subjects)
    
    # Difficulty level
    difficulty_levels = ["Mixed", "Easy", "Medium", "Hard"]
    selected_difficulty = st.sidebar.selectbox("📊 Difficulty Level", difficulty_levels)
    
    # Number of flashcards
    num_flashcards = st.sidebar.slider("🔢 Number of Flashcards", 10, 25, 15)
    
    # Language selection
    languages = ["English", "Spanish", "French", "German", "Italian"]
    selected_language = st.sidebar.selectbox("🌐 Output Language", languages)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 Input Content", "🃏 Generated Flashcards", "📤 Export"])
    
    with tab1:
        st.header("Input Your Educational Content")
        
        # Input method selection
        input_method = st.radio("Choose input method:", ["Direct Text Input", "File Upload"])
        
        content = ""
        
        if input_method == "Direct Text Input":
            content = st.text_area(
                "Paste your educational content here:",
                height=300,
                placeholder="Enter textbook excerpts, lecture notes, or any educational material..."
            )
        
        else:  # File Upload
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'pdf'],
                help="Upload .txt or .pdf files containing educational content"
            )
            
            if uploaded_file is not None:
                file_processor = FileProcessor()
                try:
                    content = file_processor.process_file(uploaded_file)
                    st.success(f"✅ File processed successfully! Content length: {len(content)} characters")
                    
                    # Show preview
                    with st.expander("📖 Content Preview"):
                        st.text(content[:1000] + "..." if len(content) > 1000 else content)
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
        
        # Generate flashcards button
        if st.button("🚀 Generate Flashcards", type="primary", disabled=not content.strip()):
            if content.strip():
                with st.spinner("🤖 AI is generating your flashcards... This may take a few minutes."):
                    try:
                        flashcards = st.session_state.generator.generate_flashcards(
                            content=content,
                            subject=selected_subject,
                            difficulty=selected_difficulty,
                            num_cards=num_flashcards,
                            language=selected_language
                        )
                        
                        st.session_state.flashcards = flashcards
                        st.success(f"✅ Generated {len(flashcards)} flashcards successfully!")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Error generating flashcards: {str(e)}")
                        st.info("💡 Try with shorter content or check your internet connection for model download.")
    
    with tab2:
        st.header("Generated Flashcards")
        
        if st.session_state.flashcards:
            st.success(f"📊 Total Flashcards: {len(st.session_state.flashcards)}")
            
            # Group by topic if available
            topics = list(set([card.get('topic', 'General') for card in st.session_state.flashcards]))
            
            if len(topics) > 1:
                selected_topic = st.selectbox("Filter by Topic:", ["All"] + topics)
                
                if selected_topic != "All":
                    filtered_cards = [card for card in st.session_state.flashcards 
                                    if card.get('topic', 'General') == selected_topic]
                else:
                    filtered_cards = st.session_state.flashcards
            else:
                filtered_cards = st.session_state.flashcards
            
            # Display flashcards
            for i, card in enumerate(filtered_cards, 1):
                with st.expander(f"🃏 Flashcard {i}: {card['question'][:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**❓ Question:**")
                        st.write(card['question'])
                        
                        # Edit question
                        new_question = st.text_area(
                            "Edit question:",
                            value=card['question'],
                            key=f"q_edit_{i}",
                            height=100
                        )
                        
                        if new_question != card['question']:
                            if st.button(f"Update Question {i}", key=f"update_q_{i}"):
                                card['question'] = new_question
                                st.success("Question updated!")
                                st.experimental_rerun()
                    
                    with col2:
                        st.markdown("**✅ Answer:**")
                        st.write(card['answer'])
                        
                        # Edit answer
                        new_answer = st.text_area(
                            "Edit answer:",
                            value=card['answer'],
                            key=f"a_edit_{i}",
                            height=100
                        )
                        
                        if new_answer != card['answer']:
                            if st.button(f"Update Answer {i}", key=f"update_a_{i}"):
                                card['answer'] = new_answer
                                st.success("Answer updated!")
                                st.experimental_rerun()
                    
                    # Additional info
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        st.caption(f"📚 Topic: {card.get('topic', 'General')}")
                    with col4:
                        st.caption(f"📊 Difficulty: {card.get('difficulty', 'Medium')}")
                    with col5:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            st.session_state.flashcards.remove(card)
                            st.success("Flashcard deleted!")
                            st.experimental_rerun()
        else:
            st.info("👆 Generate some flashcards first using the Input Content tab!")
    
    with tab3:
        st.header("Export Your Flashcards")
        
        if st.session_state.flashcards:
            exporter = FlashcardExporter()
            
            st.subheader("📤 Choose Export Format")
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Export to JSON
            with col1:
                if st.button("📄 Export to JSON"):
                    json_data = exporter.to_json(st.session_state.flashcards)
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name="flashcards.json",
                        mime="application/json"
                    )
            
            # Export to CSV
            with col2:
                if st.button("📊 Export to CSV"):
                    csv_data = exporter.to_csv(st.session_state.flashcards)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name="flashcards.csv",
                        mime="text/csv"
                    )
            
            # Export to Anki format
            with col3:
                if st.button("🧠 Export to Anki"):
                    anki_data = exporter.to_anki(st.session_state.flashcards)
                    st.download_button(
                        label="⬇️ Download Anki",
                        data=anki_data,
                        file_name="flashcards_anki.txt",
                        mime="text/plain"
                    )
            
            # Export to Quizlet format
            with col4:
                if st.button("📚 Export to Quizlet"):
                    quizlet_data = exporter.to_quizlet(st.session_state.flashcards)
                    st.download_button(
                        label="⬇️ Download Quizlet",
                        data=quizlet_data,
                        file_name="flashcards_quizlet.txt",
                        mime="text/plain"
                    )
            
            # Preview export
            st.subheader("👀 Export Preview")
            format_choice = st.selectbox("Select format to preview:", ["JSON", "CSV", "Anki", "Quizlet"])
            
            if format_choice == "JSON":
                st.code(exporter.to_json(st.session_state.flashcards), language="json")
            elif format_choice == "CSV":
                df = pd.DataFrame(st.session_state.flashcards)
                st.dataframe(df)
            elif format_choice == "Anki":
                st.text(exporter.to_anki(st.session_state.flashcards))
            elif format_choice == "Quizlet":
                st.text(exporter.to_quizlet(st.session_state.flashcards))
                
        else:
            st.info("👆 Generate some flashcards first to enable export options!")
    
    # Footer
    st.markdown("---")
    st.markdown("🤖 Powered by Hugging Face Transformers | Built with Streamlit")

if __name__ == "__main__":
    main()