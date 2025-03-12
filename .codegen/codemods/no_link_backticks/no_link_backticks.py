import codegen
from codegen import Codebase


@codegen.function(name="no-link-backticks", subdirectories=["test/unit"])
def run(codebase: Codebase):
    import re

    # Define the pattern for Markdown links with backticks in the link text
    link_pattern = re.compile(r"\[([^\]]*`[^\]]*`[^\]]*)\]\(([^)]+)\)")

    # Iterate over all .mdx files in the codebase
    for file in codebase.files(extensions=["mdx"]):
        if file.extension == ".mdx":
            print(f"Processing {file.path}")
            new_content = file.content

            # Find all markdown links with backticks in link text
            matches = link_pattern.finditer(new_content)

            for match in matches:
                # Original link text with backticks
                original_text = match.group(1)

                # Remove backticks from the link text
                new_text = original_text.replace("`", "")

                # Replace the link in content
                new_content = new_content.replace(match.group(0), f"[{new_text}]({match.group(2)})")

            # Update file content if changes were made
            if new_content != file.content:
                file.edit(new_content)

    # Commit all changes
    codebase.commit()


if __name__ == "__main__":
    print("Parsing codebase...")
    codebase = Codebase("./")

    print("Running function...")
    codegen.run(run)
