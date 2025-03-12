import codegen
from codegen import Codebase
from codegen.sdk.typescript.file import TSImport

processed_imports = set()


@codegen.function("reexport_management")
def run(codebase: Codebase):
    print("🚀 Starting reexport analysis...")
    for file in codebase.files:
        # Only process files under /src/shared
        if "examples/analize_reexports" not in file.filepath or "/src/shared" not in file.filepath:
            continue

        print(f"📁 Analyzing: {file.filepath}")

        # Gather all reexports that are not external exports
        all_reexports = []
        for export_stmt in file.export_statements:
            for export in export_stmt.exports:
                if export.is_reexport() and not export.is_external_export:
                    all_reexports.append(export)

        if not all_reexports:
            continue

        print(f"📦 Found {len(all_reexports)} reexports to process")

        for export in all_reexports:
            has_wildcard = False

            # Replace "src/" with "src/shared/"
            resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")
            print(f"🔄 Processing: {export.name} -> {resolved_public_file}")

            # Get relative path from the "public" file back to the original file
            relative_path = codebase.get_relative_path(from_file=resolved_public_file, to_file=export.resolved_symbol.filepath)

            # Ensure the "public" file exists
            if not codebase.has_file(resolved_public_file):
                print(f"✨ Creating new public file: {resolved_public_file}")
                target_file = codebase.create_file(resolved_public_file, sync=True)
            else:
                target_file = codebase.get_file(resolved_public_file)

            # If target file already has a wildcard export for this relative path, skip
            if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
                has_wildcard = True
                continue

            # Compare "public" path to the local file's export.filepath
            if codebase._remove_extension(resolved_public_file) != codebase._remove_extension(export.filepath):
                # A) Wildcard export
                if export.is_wildcard_export():
                    target_file.insert_before(f'export * from "{relative_path}"')
                    print(f"⭐ Added wildcard export for {relative_path}")

                # B) Type export
                elif export.is_type_export():
                    statement = file.get_export_statement_for_path(relative_path, "TYPE")
                    if statement:
                        if export.is_aliased():
                            statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                        else:
                            statement.insert(0, f"{export.name}")
                        print(f"📝 Updated existing type export for {export.name}")
                    else:
                        if export.is_aliased():
                            target_file.insert_before(f'export type {{ {export.resolved_symbol.name} as {export.name} }} from "{relative_path}"')
                        else:
                            target_file.insert_before(f'export type {{ {export.name} }} from "{relative_path}"')
                        print(f"✨ Added new type export for {export.name}")

                # C) Normal export
                else:
                    statement = file.get_export_statement_for_path(relative_path, "EXPORT")
                    if statement:
                        if export.is_aliased():
                            statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                        else:
                            statement.insert(0, f"{export.name}")
                        print(f"📝 Updated existing export for {export.name}")
                    else:
                        if export.is_aliased():
                            target_file.insert_before(f'export {{ {export.resolved_symbol.name} as {export.name} }} from "{relative_path}"')
                        else:
                            target_file.insert_before(f'export {{ {export.name} }} from "{relative_path}"')
                        print(f"✨ Added new export for {export.name}")

            # Update import usages
            for usage in export.symbol_usages():
                if isinstance(usage, TSImport) and usage not in processed_imports:
                    processed_imports.add(usage)

                    new_path = usage.file.ts_config.translate_import_path(resolved_public_file)

                    if has_wildcard and export.name != export.resolved_symbol.name:
                        name = f"{export.resolved_symbol.name} as {export.name}"
                    else:
                        name = usage.name

                    if usage.is_type_import():
                        new_import = f'import type {{ {name} }} from "{new_path}"'
                    else:
                        new_import = f'import {{ {name} }} from "{new_path}"'

                    usage.file.insert_before(new_import)
                    usage.remove()
                    print(f"🔄 Updated import in {usage.file.filepath}")

            # Remove old export
            export.remove()
            print(f"🗑️  Removed old export from {export.filepath}")

        # Clean up empty files
        if not file.export_statements and len(file.symbols) == 0:
            file.remove()
            print(f"🧹 Removed empty file: {file.filepath}")
        codebase.commit()


if __name__ == "__main__":
    print("🎯 Starting reexport organization...")
    codebase = Codebase("./", language="typescript")
    run(codebase)
    print("✅ Done! All reexports organized successfully!")
