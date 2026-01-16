# add_data.py
from backend.database import SessionLocal, engine
from backend.models import Question, Base

def add_questions():
    """
    连接到数据库并添加新的问题。
    """
    # 1. 如果表不存在，则创建表
    # 这可以确保在尝试添加数据之前数据库已正确设置。
    Base.metadata.create_all(bind=engine)

    # 2. 获取数据库会话
    db = SessionLocal()

    try:
        # 3. 在这里定义您想添加的新问题
        # 您可以向此列表中添加更多的 Question 对象。
        # 格式如下:
        # content="问题内容",
        # option_a="选项A",
        # option_b="选项B",
        # option_c="选项C",
        # option_d="选项D",
        # correct_answer="A" (或 "B", "C", "D")
        new_questions = [
            Question(
                content="在Python中，哪个关键字用于定义一个函数？",
                option_a="def",
                option_b="function",
                option_c="fun",
                option_d="define",
                correct_answer="A"
            ),
            Question(
                content="SQLAlchemy是一个什么库？",
                option_a="Web框架",
                option_b="数据库ORM",
                option_c="测试工具",
                option_d="前端库",
                correct_answer="B"
            ),
            # --- 在这里添加更多问题 ---
            # 示例:
            # Question(
            #     content="你的下一个问题是什么？",
            #     option_a="选项1",
            #     option_b="选项2",
            #     option_c="选项3",
            #     option_d="选项4",
            #     correct_answer="C"
            # ),
        ]

        # 4. 将新问题添加到数据库
        db.add_all(new_questions)
        db.commit()

        print(f"成功添加 {len(new_questions)} 条新问题到数据库。")

    except Exception as e:
        print(f"添加问题时发生错误: {e}")
        db.rollback()
    finally:
        # 5. 关闭会话
        db.close()

if __name__ == "__main__":
    add_questions()
