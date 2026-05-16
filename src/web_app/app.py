import re
import os
import streamlit as st
from src.workflow.graph import chat

st.set_page_config(page_title="ContentBlitz", page_icon="✍️", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []
if "generated_content" not in st.session_state:
    st.session_state.generated_content = ""

tab_chat, tab_editor, tab_images = st.tabs(["💬 Chat", "📝 Content Editor", "🖼️ Images"])

# ---- CHAT TAB ----
with tab_chat:
    st.title("✍️ ContentBlitz")
    st.caption("AI-powered content marketing assistant")

    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("agents"):
                st.caption(f"Agents used: {msg['agents']}")

    if prompt := st.chat_input("What content can I help you create?"):
        st.session_state.display_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Creating content..."):
                response, agents_used, st.session_state.chat_history = chat(
                    prompt, st.session_state.chat_history
                )
            st.markdown(response)
            st.caption(f"Agents used: {agents_used}")

            # Store the last agent's content for editor (the final content piece)
            parts = response.split("\n\n---\n\n")
            st.session_state.generated_content = parts[-1] if parts else response

        st.session_state.display_messages.append({
            "role": "assistant", "content": response, "agents": agents_used,
        })

# ---- CONTENT EDITOR TAB ----
with tab_editor:
    st.title("📝 Content Editor")
    st.caption("Edit and export your generated content")

    # Replace [IMAGE: ...] markers with actual markdown image references
    export_content = st.session_state.generated_content
    image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "generated_images")
    if os.path.exists(image_dir):
        images = sorted(
            [f for f in os.listdir(image_dir) if f.endswith(".png")],
            key=lambda f: os.path.getmtime(os.path.join(image_dir, f)),
            reverse=True,
        )
        # Replace [IMAGE: description] with markdown image syntax
        import re
        img_counter = [0]

        def replace_image_marker(match):
            desc = match.group(1)
            if img_counter[0] < len(images):
                img_file = images[img_counter[0]]
                img_counter[0] += 1
                return f"![{desc}](generated_images/{img_file})"
            return match.group(0)

        export_content = re.sub(r'\[IMAGE:\s*(.+?)\]', replace_image_marker, export_content)

    edited = st.text_area(
        "Edit your content below:",
        value=export_content,
        height=400,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "💾 Download Markdown",
            data=edited,
            file_name="content.md",
            mime="text/markdown",
        )



# ---- IMAGES TAB ----
with tab_images:
    st.title("🖼️ Generated Images")

    image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "generated_images")

    if os.path.exists(image_dir):
        images = sorted(
            [f for f in os.listdir(image_dir) if f.endswith(".png")],
            key=lambda f: os.path.getmtime(os.path.join(image_dir, f)),
            reverse=True,
        )
        if images:
            for img_file in images[:10]:
                img_path = os.path.join(image_dir, img_file)
                st.image(img_path, caption=img_file, width="stretch")
        else:
            st.info("No images generated yet. Ask the chat to create an image!")
    else:
        st.info("No images generated yet. Ask the chat to create an image!")

# ---- SIDEBAR ----
with st.sidebar:
    st.title("About ContentBlitz")
    st.markdown("""
    **ContentBlitz** is an AI-powered content marketing assistant.
    
    **Agents:**
    - 🔍 Deep Research — web research with sources
    - 📝 SEO Blog Writer — optimized long-form content
    - 💼 LinkedIn Writer — engaging professional posts
    - 🖼️ Image Generator — AI-powered visuals
    - 📊 Content Strategist — content planning
    
    **Tips:**
    - "Research X and write a blog about it"
    - "Create a LinkedIn post about Y"
    - "Generate an image for my article about Z"
    - "Create a full content package about W"
    """)

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.display_messages = []
        st.session_state.generated_content = ""
        st.rerun()