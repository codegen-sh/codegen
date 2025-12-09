import streamlit as st

from codegen import Codebase

# Page config
st.set_page_config(page_title="Codegen Repository Analyzer", page_icon="🔍", layout="wide")

st.title("🔍 GitHub Repository Analyzer")
st.markdown("""
Analyze any public GitHub repository using Codegen's powerful analysis capabilities.
This tool provides insights into the codebase structure and metrics.
""")

# Repository input in sidebar
with st.sidebar:
    st.header("Repository Settings")
    repo_name = st.text_input("GitHub Repository", value="fastapi/fastapi", help="Enter the repository name in the format 'owner/repo' (e.g. fastapi/fastapi)")
    analyze_button = st.button("🚀 Analyze Repository", use_container_width=True)

# Main content
if analyze_button:
    if "/" not in repo_name:
        st.error("⚠️ Please enter the repository name in the format 'owner/repo'")
    else:
        try:
            # Create progress container
            progress_container = st.empty()
            with progress_container.container():
                st.info("🔄 Cloning repository...")

                # Initialize codebase
                codebase = Codebase.from_repo(repo_name)

                st.info("📊 Analyzing codebase...")

                # Calculate metrics
                num_files = len(codebase.files)
                num_functions = len(codebase.functions)
                num_classes = len(codebase.classes)

                # Clear progress messages
                progress_container.empty()

                # Display success message
                st.success("✨ Analysis complete!")

                # Display metrics in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📁 Files", num_files)
                with col2:
                    st.metric("⚡ Functions", num_functions)
                with col3:
                    st.metric("🔷 Classes", num_classes)

                # Show file breakdown
                st.subheader("📊 File Types")
                file_extensions = {}
                for file in codebase.files:
                    ext = file.extension or "no extension"
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1

                # Convert to sorted list of tuples
                extension_data = sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10 extensions

                if extension_data:
                    extensions, counts = zip(*extension_data)
                    st.bar_chart({"count": counts}, height=200)
                    st.caption("Top 10 file extensions by count")

        except Exception as e:
            st.error(f"❌ Error analyzing repository: {e!s}")
            st.info("Please make sure the repository exists and is public.")

# Add helpful information at the bottom
with st.expander("How to use"):
    st.markdown("""
    1. Enter a public GitHub repository name in the format `owner/repo` in the sidebar
    2. Click "Analyze Repository" to start the analysis
    3. Wait for the results to appear

    The analyzer will:
    - Clone the repository
    - Count files, functions, and classes
    - Show distribution of file types
    - Display key metrics about the codebase

    **Note**: Only public repositories can be analyzed.
    """)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using [Codegen](https://github.com/codegen-dev/codegen)", unsafe_allow_html=True)
