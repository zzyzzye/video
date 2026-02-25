import logging
import smtplib
import traceback
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

# 配置日志
logger = logging.getLogger(__name__)

def send_verification_email(user, code, code_type):
    """
    发送验证码邮件
    
    Args:
        user: 用户对象
        code: 验证码
        code_type: 验证码类型 (email_verify, password_reset, email_change)
        
    Returns:
        bool: 是否发送成功
    """
    try:
        # 设置邮件标题
        if code_type == 'email_verify':
            subject = '邮箱验证'
        elif code_type == 'password_reset':
            subject = '密码重置'
        elif code_type == 'email_change':
            subject = '修改邮箱'
        else:
            subject = '验证码'
        
        # 邮件内容
        if code_type == 'email_verify':
            html_message = f"""
            <h2>您好，{user.username}！</h2>
            <p>感谢您注册{settings.SITE_NAME}。请使用以下验证码验证您的邮箱地址：</p>
            <h1 style="color: #3C91E6; font-size: 24px; letter-spacing: 5px;">{code}</h1>
            <p>验证码有效期为30分钟。</p>
            <p>如果您没有请求此验证码，请忽略此邮件。</p>
            <p>祝好，<br>{settings.SITE_NAME}团队</p>
            """
        elif code_type == 'password_reset':
            html_message = f"""
            <h2>您好，{user.username}！</h2>
            <p>您正在请求重置密码。请使用以下验证码完成密码重置：</p>
            <h1 style="color: #3C91E6; font-size: 24px; letter-spacing: 5px;">{code}</h1>
            <p>验证码有效期为30分钟。</p>
            <p>如果您没有请求此验证码，请忽略此邮件。</p>
            <p>祝好，<br>{settings.SITE_NAME}团队</p>
            """
        elif code_type == 'email_change':
            html_message = f"""
            <h2>您好，{user.username}！</h2>
            <p>您正在请求修改邮箱地址。请使用以下验证码完成邮箱修改：</p>
            <h1 style="color: #3C91E6; font-size: 24px; letter-spacing: 5px;">{code}</h1>
            <p>验证码有效期为30分钟。</p>
            <p>如果您没有请求此验证码，请忽略此邮件。</p>
            <p>祝好，<br>{settings.SITE_NAME}团队</p>
            """
            
        # 纯文本内容
        plain_message = strip_tags(html_message)
        
        # 记录发送前的信息
        logger.info(f"准备发送{code_type}验证码邮件到 {user.email}, 验证码: {code}")
        
        # 尝试使用直接SMTP连接发送
        try:
            logger.info(f"尝试直接连接SMTP服务器发送验证码邮件: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            
            # 创建消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = user.email
            
            # 添加纯文本和HTML内容
            part1 = MIMEText(plain_message, 'plain', 'utf-8')
            part2 = MIMEText(html_message, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # 连接SMTP服务器
            if settings.EMAIL_USE_SSL:
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
            
            # 登录
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # 发送邮件
            server.sendmail(settings.EMAIL_HOST_USER, [user.email], msg.as_string())
            
            # 关闭连接
            server.quit()
            
            logger.info(f"已通过直接SMTP连接成功发送{code_type}验证码邮件到 {user.email}")
            return True
        except Exception as direct_smtp_error:
            logger.error(f"直接SMTP连接发送验证码邮件失败: {str(direct_smtp_error)}")
            logger.error(traceback.format_exc())
            
            # 回退到Django的send_mail
            logger.info("尝试使用Django的send_mail发送验证码邮件")
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,  # 改为使用纯邮箱地址
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"已成功发送{code_type}验证码邮件到 {user.email}（通过Django send_mail）")
            return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP身份验证错误: {str(e)}")
        logger.error("请检查邮箱账号和授权码是否正确")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"发送验证码邮件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def send_test_email(email):
    """
    发送测试邮件
    
    Args:
        email: 收件人邮箱
        
    Returns:
        bool: 是否发送成功
    """
    try:
        subject = '测试邮件'
        html_message = f"""
        <h2>这是一封来自{settings.SITE_NAME}的测试邮件</h2>
        <p>如果您收到这封邮件，说明邮件系统配置正确。</p>
        <p>祝好，<br>{settings.SITE_NAME}团队</p>
        """
        plain_message = strip_tags(html_message)
        
        logger.info(f"准备发送测试邮件到 {email}")
        
        # 使用更底层的SMTP连接来获取更多信息
        try:
            logger.info(f"尝试直接连接SMTP服务器: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            
            # 创建消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_HOST_USER  # 使用纯邮箱地址
            msg['To'] = email
            
            # 添加纯文本和HTML内容
            part1 = MIMEText(plain_message, 'plain', 'utf-8')
            part2 = MIMEText(html_message, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # 连接SMTP服务器
            if settings.EMAIL_USE_SSL:
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
                
            server.set_debuglevel(1)  # 启用详细日志
            
            # 登录
            logger.info(f"尝试登录SMTP服务器，用户名: {settings.EMAIL_HOST_USER}")
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            # 发送邮件
            logger.info(f"发送邮件从 {settings.EMAIL_HOST_USER} 到 {email}")
            server.sendmail(settings.EMAIL_HOST_USER, [email], msg.as_string())
            
            # 关闭连接
            server.quit()
            logger.info("SMTP连接已关闭")
            
            logger.info(f"已通过直接SMTP连接成功发送测试邮件到 {email}")
            return True
        except Exception as direct_smtp_error:
            logger.error(f"直接SMTP连接失败: {str(direct_smtp_error)}")
            logger.error(traceback.format_exc())
            
            # 回退到Django的send_mail
            logger.info("尝试使用Django的send_mail发送")
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"已成功发送测试邮件到 {email}（通过Django send_mail）")
            return True
        
    except socket.gaierror as e:
        logger.error(f"DNS解析错误: {str(e)}")
        logger.error("请检查SMTP服务器地址是否正确")
        return False
    except socket.timeout as e:
        logger.error(f"连接超时: {str(e)}")
        logger.error("SMTP服务器连接超时，请检查网络或服务器设置")
        return False
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP身份验证错误: {str(e)}")
        logger.error("请检查邮箱账号和授权码是否正确")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"发送测试邮件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False 