import requests
import json
import sqlite3
import os
from typing import Dict, Any, Optional


class SearchAPI:
    def __init__(self, config: dict):
        self.config = config
        self.api_enabled = config.get("search_api", {}).get("enabled", True)
        self.api_url = config.get("search_api", {}).get("api_url", "")
        self.api_key = config.get("search_api", {}).get("api_key", "")
        self.timeout = config.get("search_api", {}).get("timeout", 10)
        
        self.local_enabled = config.get("local_database", {}).get("enabled", False)
        self.local_db_path = config.get("local_database", {}).get("file_path", "questions.db")
        
        # 初始化本地数据库
        if self.local_enabled:
            self._init_local_database()

    def _init_local_database(self):
        """初始化本地题库数据库"""
        conn = sqlite3.connect(self.local_db_path)
        cursor = conn.cursor()
        
        # 创建题目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                answer TEXT NOT NULL,
                options TEXT,
                question_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def search_answer(self, question_text: str, question_type: str = "") -> Dict[str, Any]:
        """搜索答案，优先使用API，其次使用本地数据库"""
        result = {
            "success": False,
            "answer": "",
            "source": "",
            "confidence": 0.0
        }

        # 优先使用API搜索
        if self.api_enabled and self.api_url:
            api_result = self._search_via_api(question_text, question_type)
            if api_result["success"]:
                return api_result

        # 使用本地数据库搜索
        if self.local_enabled:
            local_result = self._search_via_local(question_text)
            if local_result["success"]:
                return local_result

        return result

    def _search_via_api(self, question_text: str, question_type: str = "") -> Dict[str, Any]:
        """通过第三方API搜索答案"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }

            # 构建请求参数
            payload = {
                "question": question_text,
                "type": question_type,
                "key": self.api_key
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            # 解析API返回结果（通用格式）
            if data.get("success") or data.get("code") == 0:
                answer = data.get("answer", "")
                if not answer:
                    answer = data.get("data", {}).get("answer", "")
                
                return {
                    "success": True,
                    "answer": answer,
                    "source": "api",
                    "confidence": data.get("confidence", 0.8)
                }

        except Exception as e:
            print(f"API搜索失败: {e}")

        return {
            "success": False,
            "answer": "",
            "source": "api",
            "confidence": 0.0
        }

    def _search_via_local(self, question_text: str) -> Dict[str, Any]:
        """通过本地数据库搜索答案"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()

            # 使用模糊匹配搜索
            cursor.execute('''
                SELECT content, answer, question_type 
                FROM questions 
                WHERE content LIKE ? 
                ORDER BY LENGTH(content) DESC
                LIMIT 1
            ''', (f"%{question_text[:50]}%",))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    "success": True,
                    "answer": result[1],
                    "source": "local",
                    "confidence": 0.9
                }

        except Exception as e:
            print(f"本地数据库搜索失败: {e}")

        return {
            "success": False,
            "answer": "",
            "source": "local",
            "confidence": 0.0
        }

    def add_to_local_database(self, question_content: str, answer: str, 
                             question_type: str = "", options: str = ""):
        """将题目添加到本地数据库"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO questions (content, answer, options, question_type)
                VALUES (?, ?, ?, ?)
            ''', (question_content, answer, options, question_type))

            conn.commit()
            conn.close()
            print(f"题目已添加到本地数据库: {question_content[:30]}...")

        except Exception as e:
            print(f"添加到本地数据库失败: {e}")

    def get_local_statistics(self) -> Dict[str, int]:
        """获取本地数据库统计信息"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM questions")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type")
            by_type = dict(cursor.fetchall())

            conn.close()

            return {
                "total": total,
                **by_type
            }

        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"total": 0}


"""
第三方搜题API对接说明：

【通用API接口格式】
大多数第三方搜题API采用以下格式：

1. 请求方式：POST
2. Content-Type: application/json
3. 请求参数：
   {
       "question": "题目内容",
       "type": "question_type"  // 可选：single/multiple/judge/fill
   }

4. 响应格式：
   {
       "success": true,
       "answer": "答案内容",
       "confidence": 0.95
   }

【对接示例】
以某搜题API为例：
1. 在config.json中配置：
   "search_api": {
       "enabled": true,
       "api_url": "https://api.example.com/search",
       "api_key": "your_api_key_here",
       "timeout": 10
   }

2. API返回示例：
   {
       "success": true,
       "data": {
           "answer": "A",
           "options": ["A. 选项1", "B. 选项2"]
       }
   }

【注意事项】
1. API密钥保护：不要将API密钥硬编码在代码中，使用配置文件
2. 请求频率限制：避免频繁请求导致IP被封禁
3. 数据合法性：确保使用的API服务合法合规
4. 错误处理：添加重试机制和异常捕获
5. 敏感信息：不要在日志中记录完整的API响应

【本地题库使用】
1. 在config.json中启用本地数据库：
   "local_database": {
       "enabled": true,
       "file_path": "questions.db"
   }

2. 手动添加题目到本地数据库：
   使用 search_api.add_to_local_database() 方法

3. 本地数据库会自动创建，存储在程序运行目录下的 questions.db 文件中
"""