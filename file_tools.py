import os
import json
import glob
import shutil
from typing import Dict, List, Any, Optional

async def file_read(path: str, offset: int = 0, limit: int = 1000) -> Dict:
    """Read file contents."""
    try:
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            if offset > 0:
                for _ in range(offset):
                    f.readline()
            lines = []
            for i, line in enumerate(f):
                if i >= limit:
                    break
                lines.append(line.rstrip('\n'))

        return {
            "path": path,
            "content": '\n'.join(lines),
            "offset": offset,
            "lines_read": len(lines),
            "total_size": os.path.getsize(path)
        }
    except Exception as e:
        return {"error": str(e)}

async def file_write(path: str, content: str, append: bool = False) -> Dict:
    """Write content to file."""
    try:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        return {
            "path": path,
            "action": "append" if append else "write",
            "bytes_written": len(content.encode('utf-8')),
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}

async def file_list(directory: str = ".", pattern: str = "*", recursive: bool = False) -> Dict:
    """List files in directory."""
    try:
        if recursive:
            files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        else:
            files = glob.glob(os.path.join(directory, pattern))

        files = [f for f in files if os.path.isfile(f)]
        file_info = []
        for f in files[:100]:  # Limit to 100 files
            stat = os.stat(f)
            file_info.append({
                "path": f,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })

        return {
            "directory": directory,
            "pattern": pattern,
            "recursive": recursive,
            "files": file_info,
            "count": len(file_info)
        }
    except Exception as e:
        return {"error": str(e)}

async def file_search(directory: str, query: str, file_pattern: str = "*") -> Dict:
    """Search for text in files."""
    try:
        matches = []
        for root, _, files in os.walk(directory):
            for file in files:
                if not glob.fnmatch.fnmatch(file, file_pattern):
                    continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if query in content:
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if query in line:
                                    matches.append({
                                        "file": filepath,
                                        "line": i + 1,
                                        "content": line.strip()
                                    })
                except:
                    continue

        return {
            "query": query,
            "directory": directory,
            "matches": matches[:50],
            "total_matches": len(matches)
        }
    except Exception as e:
        return {"error": str(e)}

async def file_delete(path: str) -> Dict:
    """Delete file or directory."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return {"path": path, "type": "file", "deleted": True}
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return {"path": path, "type": "directory", "deleted": True}
        else:
            return {"error": f"Path not found: {path}"}
    except Exception as e:
        return {"error": str(e)}

async def file_move(source: str, destination: str) -> Dict:
    """Move or rename file."""
    try:
        os.makedirs(os.path.dirname(destination) or '.', exist_ok=True)
        shutil.move(source, destination)
        return {"source": source, "destination": destination, "success": True}
    except Exception as e:
        return {"error": str(e)}

async def file_copy(source: str, destination: str) -> Dict:
    """Copy file."""
    try:
        os.makedirs(os.path.dirname(destination) or '.', exist_ok=True)
        shutil.copy2(source, destination)
        return {"source": source, "destination": destination, "success": True}
    except Exception as e:
        return {"error": str(e)}

async def file_info(path: str) -> Dict:
    """Get file information."""
    try:
        stat = os.stat(path)
        return {
            "path": path,
            "exists": os.path.exists(path),
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "permissions": oct(stat.st_mode)[-3:]
        }
    except Exception as e:
        return {"error": str(e)}
