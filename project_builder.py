#!/usr/bin/env python3
"""
Project Builder - Reconstructs projects from AI-generated export files.
No path filtering - accepts all valid file paths including Next.js dynamic routes.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Language mapping
LANG_MAP = {
    '.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript', '.jsx': 'JavaScript',
    '.py': 'Python', '.java': 'Java', '.kt': 'Kotlin', '.swift': 'Swift',
    '.rs': 'Rust', '.go': 'Go', '.rb': 'Ruby', '.php': 'PHP', '.cs': 'C#',
    '.c': 'C', '.cpp': 'C++', '.h': 'C', '.hpp': 'C++',
    '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS', '.sass': 'Sass',
    '.json': 'JSON', '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML',
    '.md': 'Markdown', '.txt': 'Text', '.sql': 'SQL', '.mod': 'Go Module',
    '.env': 'Environment', '.prisma': 'Prisma', '.sh': 'Shell', '.bash': 'Shell',
    '.dart': 'Dart', '.toml': 'TOML', '.graphql': 'GraphQL',
}

CODE_LANG_MAP = {
    'go': 'Go', 'golang': 'Go', 'python': 'Python', 'py': 'Python',
    'javascript': 'JavaScript', 'js': 'JavaScript', 'typescript': 'TypeScript',
    'ts': 'TypeScript', 'tsx': 'TypeScript', 'java': 'Java',
    'json': 'JSON', 'yaml': 'YAML', 'yml': 'YAML', 'xml': 'XML',
    'html': 'HTML', 'css': 'CSS', 'scss': 'SCSS', 'shell': 'Shell',
    'bash': 'Shell', 'markdown': 'Markdown', 'md': 'Markdown',
    'text': 'Text', '': 'Text',
}


class ProjectBuilder:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir).resolve()
        self.files_created = 0
        self.errors: List[str] = []
    
    def get_language(self, filepath: str, code_lang: Optional[str] = None) -> str:
        """Get language from code fence or file extension."""
        if code_lang:
            lang = code_lang.lower().strip()
            if lang in CODE_LANG_MAP:
                return CODE_LANG_MAP[lang]
        
        ext = Path(filepath).suffix.lower()
        if ext in LANG_MAP:
            return LANG_MAP[ext]
        
        name = Path(filepath).name.lower()
        if name == 'dockerfile':
            return 'Dockerfile'
        if name == 'makefile':
            return 'Makefile'
        if name.startswith('.env'):
            return 'Environment'
        if name == '.gitignore':
            return 'Git Ignore'
        if name == 'go.mod':
            return 'Go Module'
        if name == 'go.sum':
            return 'Go Sum'
        
        return 'Text'
    
    def clean_path(self, path: str) -> str:
        """Normalize file path - remove quotes, backticks, extra chars."""
        path = path.strip()
        # Remove backticks, quotes, hash symbols from start/end only
        path = re.sub(r'^[`#\'"]+|[`#\'"]+$', '', path).strip()
        # Remove "File:", "Path:", etc.
        path = re.sub(r'^(file|path|filename):\s*', '', path, flags=re.IGNORECASE).strip()
        # Normalize slashes
        path = path.replace('\\', '/')
        while '//' in path:
            path = path.replace('//', '/')
        if path.startswith('./'):
            path = path[2:]
        return path
    
    def clean_content(self, content: str) -> str:
        """Clean file content."""
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        return content.strip()
    
    def is_valid_path(self, path: str) -> bool:
        """Check if path looks like a valid file path."""
        if not path:
            return False
        # Should contain at least one dot or slash
        if '.' not in path and '/' not in path and '\\' not in path:
            return False
        if len(path) > 500:
            return False
        return True
    
    def parse_export_file(self, filepath: str) -> List[Dict]:
        """Parse export file with multiple format support."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        files = []
        lines = content.split('\n')
        
        current_file: Optional[Dict] = None
        in_code_block = False
        code_block_lang = ''
        code_block_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code block start/end
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_lang = line.strip()[3:].strip()
                    code_block_content = []
                else:
                    in_code_block = False
                    if current_file and code_block_content:
                        current_file['content'] = self.clean_content('\n'.join(code_block_content))
                        current_file['language'] = self.get_language(
                            current_file['path'], 
                            code_block_lang if code_block_lang else current_file.get('language')
                        )
                        files.append(current_file)
                        current_file = None
                    code_block_lang = ''
                i += 1
                continue
            
            if in_code_block:
                code_block_content.append(line)
                i += 1
                continue
            
            file_path = None
            
            # Pattern 1: ### `filename` or ## `filename` or # `filename`
            match = re.match(r'^#{1,6}\s*[`"\']?([^`"\n\'#]+)[`"\']?\s*$', line)
            if match:
                potential_path = self.clean_path(match.group(1))
                if self.is_valid_path(potential_path):
                    file_path = potential_path
            
            # Pattern 2: ### filename (without backticks)
            if not file_path:
                match = re.match(r'^#{1,6}\s+([a-zA-Z0-9_./\\[\]\-]+\.[a-zA-Z0-9]+)\s*$', line)
                if match:
                    potential_path = self.clean_path(match.group(1))
                    if self.is_valid_path(potential_path):
                        file_path = potential_path
            
            # Pattern 3: **filename** or __filename__
            if not file_path:
                match = re.match(r'^\*{2}([a-zA-Z0-9_./\\[\]\-]+\.[a-zA-Z0-9]+)\*{2}\s*$', line)
                if match:
                    potential_path = self.clean_path(match.group(1))
                    if self.is_valid_path(potential_path):
                        file_path = potential_path
            
            # Pattern 4: `filename` on its own line
            if not file_path:
                match = re.match(r'^`([a-zA-Z0-9_./\\[\]\-]+\.[a-zA-Z0-9]+)`\s*$', line)
                if match:
                    potential_path = self.clean_path(match.group(1))
                    if self.is_valid_path(potential_path):
                        file_path = potential_path
            
            # Pattern 5: File: path/to/file or Path: path/to/file
            if not file_path:
                match = re.match(r'^(?:file|path|filename):\s*([a-zA-Z0-9_./\\[\]\-]+\.[a-zA-Z0-9]+)\s*$', line, re.IGNORECASE)
                if match:
                    potential_path = self.clean_path(match.group(1))
                    if self.is_valid_path(potential_path):
                        file_path = potential_path
            
            if file_path:
                if current_file and current_file.get('content'):
                    files.append(current_file)
                
                current_file = {
                    'path': file_path,
                    'language': self.get_language(file_path),
                    'content': ''
                }
            
            i += 1
        
        # Handle content without code blocks
        if not files and current_file:
            for i, line in enumerate(lines):
                if re.match(r'^#{1,6}\s+', line):
                    continue
                if line.strip() and not line.strip().startswith('```'):
                    content_lines = []
                    for j in range(i, len(lines)):
                        if re.match(r'^#{1,6}\s+', lines[j]):
                            break
                        content_lines.append(lines[j])
                    
                    if content_lines and current_file:
                        current_file['content'] = self.clean_content('\n'.join(content_lines))
                        files.append(current_file)
                    break
        
        # Remove duplicates (keep last)
        seen = {}
        for f in files:
            if f['path'] and f['content']:
                seen[f['path']] = f
        files = list(seen.values())
        
        return files
    
    def create_file(self, file_info: Dict) -> bool:
        """Create a single file - NO PATH FILTERING."""
        try:
            rel_path = Path(file_info['path'])
            full_path = self.output_dir / rel_path
            
            # Create parent directories (handles Next.js [brackets] fine)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_info['content'])
            
            self.files_created += 1
            print(f"  ✓ {file_info['path']}")
            return True
            
        except Exception as e:
            self.errors.append(f"Failed {file_info['path']}: {str(e)}")
            print(f"  ✗ {file_info['path']} - {str(e)}")
            return False
    
    def build(self, export_file: str) -> bool:
        """Main build process."""
        print(f"\n🔍 Parsing: {export_file}")
        
        if not Path(export_file).exists():
            print(f"❌ Error: File not found: {export_file}")
            return False
        
        files = self.parse_export_file(export_file)
        
        if not files:
            print("\n❌ No files found. Check the format.")
            print("\nSupported formats:")
            print("  ### `filename.ext`")
            print("  ## filename.ext")
            print("  **filename.ext**")
            print("  `filename.ext`")
            print("  File: filename.ext")
            print("\nFollowed by:")
            print("  ```lang")
            print("  content")
            print("  ```")
            return False
        
        print(f"📦 Found {len(files)} files")
        print(f"📁 Output: {self.output_dir}")
        print("\n🔨 Creating:")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_info in files:
            self.create_file(file_info)
        
        print(f"\n{'='*60}")
        print(f"✅ Complete! Created {self.files_created}/{len(files)} files")
        
        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for err in self.errors[:3]:
                print(f"   • {err}")
        
        return self.files_created > 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Reconstruct project from AI-generated export file'
    )
    parser.add_argument('export_file', nargs='?', help='Export file to parse')
    parser.add_argument('-o', '--output', default='.', help='Output directory')
    parser.add_argument('-n', '--name', help='Project folder name')
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    
    args = parser.parse_args()
    
    if not args.export_file:
        print("Usage: python build_project.py <export_file.md> [-o output_dir] [-n project_name]")
        print("Example: python build_project.py codepoiolet.md -o ./codepilot")
        sys.exit(1)
    
    output_path = Path(args.output)
    if args.name:
        output_path = output_path / args.name
    
    print("="*60)
    print("🚀 Project Builder - No Path Filtering")
    print("="*60)
    
    builder = ProjectBuilder(str(output_path))
    
    if args.dry_run:
        files = builder.parse_export_file(args.export_file)
        print(f"\n📋 Would create {len(files)} files:")
        for f in files[:20]:
            print(f"   • {f['path']} [{f['language']}]")
        if len(files) > 20:
            print(f"   ... and {len(files) - 20} more")
    else:
        success = builder.build(args.export_file)
        if success:
            print(f"\n🎉 Project ready: {output_path}")
            print(f"💡 Next: cd {output_path} && ls -la")
    
    return 0 if builder.files_created > 0 else 1


if __name__ == '__main__':
    sys.exit(main())