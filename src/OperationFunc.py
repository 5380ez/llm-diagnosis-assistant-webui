# 登录逻辑
from src import database
import gradio as gr
from Model import ask_medical_llm

def handle_login(username, password):
    user_id = database.authenticate_user(username, password)
    if user_id:
        return (
            "",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            (user_id, username)
        )
    else:
        return "❌ 用户名或密码错误", gr.update(), gr.update(), gr.update(visible=False), None, ""


# 注册逻辑
def handle_register(username, password):
    ok, this_msg = database.register_user(username, password)
    return this_msg, gr.update(visible=True) if ok else gr.update()

# 查询文件逻辑
def handle_query_files(user):
    if not user:
        return "❌ 请先登录", None

    files = database.get_user_files(user[0])
    file_data = [
        [f["name"], f"📥 下载"]
        for f in files
    ]

    if not file_data:
        # 如果没有文件，返回提示行
        return [["⚠️ 无历史病历", ""]]

    return file_data

# 文件下载逻辑
def handle_file_selection(user, data, evt: gr.SelectData):
    """处理文件选择并显示下载组件"""
    try:
        # 检查用户是否登录
        if not user:
            return gr.File(visible=False)

        # 获取选中的行索引
        selected_idx = evt.index[0] if isinstance(evt.index, tuple) else evt.index
        row_index = selected_idx[0]

        # 获取选中的行数据
        # selected_data = data.iat[selected_idx[0], selected_idx[1]]
        selected_row = data.iloc[row_index]
        # print(selected_row)

        # 行数据分两个，[file_name, button]
        # 从行数据中提取file_name
        # 获取文件路径
        file_path = database.get_file_by_filename(selected_row[0])
        if file_path and os.path.exists(file_path):
            # 返回可见的文件下载组件
            return gr.File(
                value=file_path,
                visible=True,
                label=f"下载文件: {selected_row[0]}"
            )

        return gr.File(visible=False)

    except Exception as e:
        print(f"文件选择错误: {e}")
        return gr.File(visible=False)


# 调用本地模型
def chat(user_input, history):
    print("--------------已开启新一轮调用--------------")
    result = ask_medical_llm(user_input)
    # 用于模型记录输出
    medical_data = {}
    medical_data.update(result)

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content":
        "主诉：" + result["chief_complaint"] + "\n" +
        "辅助检查：" + result["examinations"] + "\n" +
        "诊断：" + result["diagnosis"] + "\n" +
        "处置意见：" + result["disposal"]})

    print("--------------history--------------")
    return "", history, result["chief_complaint"], result["examinations"], result["diagnosis"], result["disposal"]

# 生成PDF
from TextToPDF import TextToPDF
def generate_pdf(this_name, this_gender, this_age, this_phone,
                 chief, exam, diag, disp, this_current_user):
    # this_current_user: [user_id, username]
    print("正在准备保存为PDF...")
    saved_pdf = TextToPDF(this_name, this_gender, this_age, this_phone,
                         chief_complaint=chief,
                         examinations=exam,
                         diagnosis=diag,
                         disposal=disp, username=this_current_user[1])
    pdf_filename = saved_pdf[1]
    pdf_path = saved_pdf[0]
    user_id = this_current_user[0]
    database.add_user_file(user_id, pdf_filename)
    return pdf_path


# 支持用户上传图片（例如影像报告）
import shutil
import os
def save_uploaded_image(image_path):
    if image_path is None or not os.path.exists(image_path):
        return None

    save_dir = "UploadedImages"
    os.makedirs(save_dir, exist_ok=True)

    filename = os.path.basename(image_path)
    save_path = os.path.join(save_dir, filename)

    shutil.copy(image_path, save_path)
    print(f"图片已保存到：{save_path}")

    return save_path  # 用于在界面上显示