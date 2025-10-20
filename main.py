import httpx
import json
import re
import time
import asyncio
import qrcode
from io import BytesIO
from datetime import datetime
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Image


violationdata = {
    "LOCKTOWER_REASON_SMART_63": {"reason": 63, "type": 1, "reasonDesc": "", "title": "该QQ账号存在安全风险，已被安全保护。", "description": "根据系统检测，该QQ账号存在安全风险，已被安全保护。", "eDescription": "根据系统检测，该QQ账号存在安全风险，已被安全保护。", "button": "申请立即解冻", "link": ""},
    "LOCKTOWER_REASON_SMART_60": {"reason": 60, "type": 1, "reasonDesc": "", "title": "你的QQ账号因密码泄露已被系统冻结保护，请修改密码恢复使用。", "description": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "eDescription": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "button": "修改密码立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_40": {"reason": 40, "type": 2, "reasonDesc": "发布/传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播违法违规信息，已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_33": {"reason": 33, "type": 2, "reasonDesc": "", "title": "你的QQ账号因存在高被盗风险已被系统冻结保护，请修改密码恢复使用。", "description": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "eDescription": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "button": "修改密码立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_42": {"reason": 42, "type": 2, "reasonDesc": "", "title": "你的QQ账号因存在高被盗风险已被系统冻结保护，请修改密码恢复使用。", "description": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "eDescription": "系统根据智能检测或人工审核等方式判断，你的QQ账号密码已经泄露。为避免产生损失，请按照系统指引修改密码。修改成功后即可解除冻结及正常使用。", "button": "修改密码立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_10": {"reason": 10, "type": 3, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录QQ。", "description": "该QQ账号因启动号码保护被暂时冻结，请按照系统指引解除冻结。", "eDescription": "该QQ账号因启动号码保护被暂时冻结，请按照系统指引解除冻结。", "button": "申请立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_21": {"reason": 21, "type": 3, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录及使用QQ。", "description": "该QQ账号因被用户暂时冻结，已进入保护模式，请按照系统指引修改密码。修改成功后方可解除冻结及正常使用。", "eDescription": "该QQ账号因被用户暂时冻结，已进入保护模式，请按照系统指引修改密码。修改成功后方可解除冻结及正常使用。", "button": "申请立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_27": {"reason": 27, "type": 3, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录及使用QQ。", "description": "该QQ账号因用户申请注销被暂时冻结", "eDescription": "该QQ账号因用户申请注销被暂时冻结", "button": "申请立即解冻", "link": "我的QQ账号为什么会被冻结保护？"},
    "LOCKTOWER_REASON_SMART_1": {"reason": 1, "type": 4, "reasonDesc": "发布/传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播违法违规信息，已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播违法违规信息，已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_2": {"reason": 2, "type": 4, "reasonDesc": "异常添加好友", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌异常添加好友，已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌异常添加好友，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌异常添加好友，已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_3": {"reason": 3, "type": 4, "reasonDesc": "违规注册QQ账号", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌违规注册QQ账号已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌违规注册QQ账号，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌违规注册QQ账号已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_4": {"reason": 4, "type": 4, "reasonDesc": "传播色情、暴力、敏感信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播色情、暴力、敏感信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播色情、暴力、敏感信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播色情、暴力、敏感信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_5": {"reason": 5, "type": 4, "reasonDesc": "传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_6": {"reason": 6, "type": 4, "reasonDesc": "传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_28": {"reason": 28, "type": 4, "reasonDesc": "传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_7": {"reason": 7, "type": 4, "reasonDesc": "传播诈骗信息或涉嫌诈骗行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播诈骗信息或涉嫌诈骗行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播诈骗信息或涉嫌诈骗行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播诈骗信息或涉嫌诈骗行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_12": {"reason": 12, "type": 4, "reasonDesc": "传播诈骗信息或涉嫌诈骗行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播诈骗信息或涉嫌诈骗行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_13": {"reason": 13, "type": 4, "reasonDesc": "传播诈骗信息或涉嫌诈骗行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播诈骗信息或涉嫌诈骗行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_14": {"reason": 14, "type": 4, "reasonDesc": "传播诈骗信息或涉嫌诈骗行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播诈骗信息或涉嫌诈骗行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌诈骗信息或涉嫌诈骗行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_8": {"reason": 8, "type": 4, "reasonDesc": "发布/传播违法违规交易信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播违法违规交易信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播违法违规交易信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌涉嫌发布/传播违法违规交易信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_9": {"reason": 9, "type": 4, "reasonDesc": "传播违法违规信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_11": {"reason": 11, "type": 4, "reasonDesc": "业务违规操作（如批量登录等）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌业务违规操作（如批量登录等），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_15": {"reason": 15, "type": 4, "reasonDesc": "业务违规操作（如批量登录等）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌业务违规操作（如批量登录等），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_20": {"reason": 20, "type": 4, "reasonDesc": "异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_29": {"reason": 29, "type": 4, "reasonDesc": "业务违规操作（如批量登录等）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌业务违规操作（如批量登录等），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌业务违规操作（如批量登录等）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_30": {"reason": 30, "type": 4, "reasonDesc": "异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_31": {"reason": 31, "type": 4, "reasonDesc": "异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动），违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因存在异常使用行为（如涉嫌批量登录等业务违规操作、传播违法违规信息或组织相关活动）已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_22": {"reason": 22, "type": 4, "reasonDesc": "使用恶意插件", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用恶意插件已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌使用恶意插件，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用恶意插件已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_23": {"reason": 23, "type": 4, "reasonDesc": "使用恶意插件", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用恶意插件已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌使用恶意插件，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用恶意插件已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_24": {"reason": 24, "type": 4, "reasonDesc": "存在违法违规行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌存在违法违规行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌存在违法违规行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌存在违法违规行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_32": {"reason": 32, "type": 4, "reasonDesc": "使用抢红包插件", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用抢红包插件已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌使用抢红包插件，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌使用抢红包插件已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_34": {"reason": 34, "type": 4, "reasonDesc": "进行异常操作行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行异常操作行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌进行异常操作行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行异常操作行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_41": {"reason": 41, "type": 4, "reasonDesc": "违反相关法律法规或用户协议等", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌违反相关法律法规或用户协议等已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌违反相关法律法规或用户协议等，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌违反相关法律法规或用户协议等已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_43": {"reason": 43, "type": 4, "reasonDesc": "发布/传播诈骗信息或涉嫌诈骗行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诈骗信息或涉嫌诈骗行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播诈骗信息或涉嫌诈骗行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诈骗信息或涉嫌诈骗行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_44": {"reason": 44, "type": 4, "reasonDesc": "涉嫌色情、暴力、敏感信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播色情、暴力、敏感信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播色情、暴力、敏感信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播色情、暴力、敏感信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_45": {"reason": 45, "type": 4, "reasonDesc": "传播诋毁、辱骂等信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播诋毁、辱骂等信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播诋毁、辱骂等信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播诋毁、辱骂等信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_46": {"reason": 46, "type": 4, "reasonDesc": "传播赌博信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播赌博信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播赌博信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播赌博信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_47": {"reason": 47, "type": 4, "reasonDesc": "发布违禁品及相关信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布违禁品及相关信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布违禁品及相关信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布违禁品及相关信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_48": {"reason": 48, "type": 4, "reasonDesc": "传播不良信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播不良信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播不良信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播不良信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_49": {"reason": 49, "type": 4, "reasonDesc": "传播不良信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播不实信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播不良信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播不实信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_50": {"reason": 50, "type": 4, "reasonDesc": "发布/传播诋毁、辱骂等侵权信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_51": {"reason": 51, "type": 4, "reasonDesc": "发布/传播诋毁、辱骂等侵权信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播诋毁、辱骂等侵权信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_52": {"reason": 52, "type": 4, "reasonDesc": "发布/传播知识产权侵权信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播知识产权侵权信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播知识产权侵权信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播知识产权侵权信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_53": {"reason": 53, "type": 4, "reasonDesc": "发布/传播侵犯他人隐私权、肖像权、名誉权、姓名权、名称权等侵权信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播侵犯他人隐私权、肖像权、名誉权、姓名权、名称权等侵权信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播侵犯他人隐私权、肖像权、名誉权、姓名权、名称权等侵权信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播侵犯他人隐私权、肖像权、名誉权、姓名权、名称权等侵权信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_54": {"reason": 54, "type": 4, "reasonDesc": "传播违法违规信息或存在违法违规行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息或存在违法违规行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息或存在违法违规行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息或存在违法违规行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_55": {"reason": 55, "type": 4, "reasonDesc": "进行资金盗用等违法违规行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行资金盗用等违法违规行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌进行资金盗用等违法违规行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行资金盗用等违法违规行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_56": {"reason": 56, "type": 4, "reasonDesc": "进行业务违规操作", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行业务违规操作已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌进行业务违规操作，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌进行业务违规操作已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_57": {"reason": 57, "type": 4, "reasonDesc": "发布/传播垃圾/骚扰信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播垃圾/骚扰信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌发布/传播垃圾/骚扰信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌发布/传播垃圾/骚扰信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_58": {"reason": 58, "type": 4, "reasonDesc": "传播病毒、木马等恶意文件", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播病毒、木马等恶意文件已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播病毒、木马等恶意文件，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播病毒、木马等恶意文件已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_59": {"reason": 59, "type": 4, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "系统根据智能检测或人工审核等方式判断，该账号因使用非官方QQ软件被暂时冻结，请按照指引解除冻结。", "eDescription": "系统根据智能检测或人工审核等方式判断，该账号因使用非官方QQ软件被暂时冻结，请按照指引解除冻结。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "系统根据智能检测或人工审核等方式判断，该账号因使用非官方QQ软件被永久冻结，请按照指引解除冻结。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_61": {"reason": 61, "type": 4, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "该账号因涉及欺诈，被国务院打击治理电信网络新型违法犯罪工作部际联席会议办公室通报冻结，请按照指引解除冻结。", "eDescription": "该账号因涉及欺诈，被国务院打击治理电信网络新型违法犯罪工作部际联席会议办公室通报冻结，请按照指引解除冻结。", "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_61_1": {"reason": 61, "type": 4, "reasonDesc": "", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "该账号因涉及欺诈，违反了国家法规政策和《QQ号码规则》，被国务院打击治理电信网络新型违法犯罪工作部际联席会议办公室通报冻结，请按照指引解除冻结", "eDescription": "该账号因涉及欺诈，违反了国家法规政策和《QQ号码规则》，被国务院打击治理电信网络新型违法犯罪工作部际联席会议办公室通报冻结，请按照指引解除冻结", "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_62": {"reason": 62, "type": 4, "reasonDesc": "敏感信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号资料因涉嫌敏感信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号资料因涉嫌敏感信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息或组织相关活动/存在异常使用行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_66": {"reason": 66, "type": 4, "reasonDesc": "传播未成年色情信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播未成年色情信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播未成年色情信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播未成年色情信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_67": {"reason": 67, "type": 4, "reasonDesc": "传播损害未成年权益信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播损害未成年权益信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播损害未成年权益信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播损害未成年权益信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_68": {"reason": 68, "type": 4, "reasonDesc": "传播网络水军信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播网络水军信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播网络水军信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播网络水军信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_69": {"reason": 69, "type": 4, "reasonDesc": "传播网络暴力信息或组织相关活动", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播网络暴力信息或组织相关活动已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播网络暴力信息或组织相关活动，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播网络暴力信息或组织相关活动已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_70": {"reason": 70, "type": 4, "reasonDesc": "传播饭圈文化乱象等有害信息", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播饭圈文化乱象等有害信息已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播饭圈文化乱象等有害信息，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播饭圈文化乱象等有害信息已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"},
    "LOCKTOWER_REASON_SMART_OTHER": {"reason": 999, "type": 5, "reasonDesc": "传播违法违规信息或组织相关活动/存在异常使用行为", "title": "该QQ账号暂时被冻结，无法正常登录QQ，请按照指引恢复使用。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息或组织相关活动/存在异常使用行为已被暂时冻结QQ登录。请后续注册或使用QQ账号时遵守《QQ号码规则》和互联网相关法律法规。", "eDescription": "该账号因涉嫌传播违法违规信息或组织相关活动/存在异常使用行为，违反了国家法规政策和《QQ号码规则》中“内容规范”的相关规定，且该账号已于XXXX年X月X日收到QQ安全提醒并承诺不再违规。由于未遵守承诺再次违规，该账号现已被暂时冻结QQ登录。", "forever": {"title": "该QQ账号已被永久冻结，无法正常登录QQ。", "description": "根据用户举报、智能检测或人工审核等方式判断，该QQ账号因涉嫌传播违法违规信息或组织相关活动/存在异常使用行为已被永久冻结QQ登录。"}, "button": "申请立即解冻", "link": "哪些情况会导致账号被冻结？"}
}

violationlist = list(violationdata.values())


@register(
    "astrbot_plugin_violation_record",
    "Futureppo",
    "QQ查询违规插件",
    "0.0.1",
    "https://github.com/Futureppo/astrbot_plugin_violation_record",
)

class ViolationRecordPlugin(Star):
    """
    查询QQ账号违规记录的插件。
    """

    def __init__(self, context: Context):
        super().__init__(context)
        self.headers = {
            'qua': 'V1_HT5_QDT_0.70.2209190_x64_0_DEV_D',
            'host': 'q.qq.com',
            'accept': 'application/json',
            'content-type': 'application/json'
        }
    
    async def get_login_code(self) -> str:
        """获取登录二维码代码"""
        url = "https://q.qq.com/ide/devtoolAuth/GetLoginCode"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            result = response.json()
            
            if result.get("data") and result["data"].get("code"):
                return result["data"]["code"]
            else:
                raise Exception(f"获取登录二维码失败: {result.get('message', '未知错误')}")
    
    async def check_login_code(self, logincode: str) -> tuple[bool, str]:
        """轮询二维码扫描状态并获取ticket"""
        url = f"https://q.qq.com/ide/devtoolAuth/syncScanSateGetTicket?code={logincode}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            result = response.json()
            

            if result.get("code") != 0:
                logger.debug(f"轮询状态: code={result.get('code')}, message={result.get('message')}")
                return False, ""
            
            data = result.get("data", {})
            if data.get("ok") == 1 and data.get("ticket"):
                return True, data["ticket"]
            
            return False, ""
    
    async def get_code_from_ticket(self, ticket: str) -> str:
        """用 ticket 换取 code"""
        url = "https://q.qq.com/ide/login"
        
        data = {
            "appid": 1109907872,
            "ticket": ticket
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            result = response.json()
            
            if result.get("code"):
                return result["code"]
            
            raise Exception(f"获取 code 失败: {result.get('message', '未知错误')}")
    
    async def get_token_from_code(self, code: str, appid: int = 1109907872) -> dict:
        """用 code 换取 minico_token 等信息"""
        url = "https://minico.qq.com/minico/oauth20?uin=QQ%E5%AE%89%E5%85%A8%E4%B8%AD%E5%BF%83"
        
        data = {
            "code": code,
            "appid": appid,
            "platform": "qq"
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            result = response.json()
            
            if result.get("retcode") == 0 and result.get("data"):
                data = result["data"]
                
                logger.debug(f"OAuth20 返回的原始数据: {data}")
                
                auth_info = {
                    "appid": appid,
                    **data
                }
                
                # 重命名 minico_token 为 token
                if "minico_token" in auth_info:
                    auth_info["token"] = auth_info.pop("minico_token")
                
                if "expire" in auth_info:
                    del auth_info["expire"]
                
                # logger.debug(f"最终认证信息: {auth_info}")
                return auth_info
            
            raise Exception(f"获取 token 失败 [{result.get('retcode')}]: {result.get('message', '未知错误')}")
    
    async def get_record(self, auth_data: dict, num: int = 20) -> dict:
        """查询违规记录"""
        params = {**auth_data}
        if "appid" not in params:
            params["appid"] = 1109907872

        param_str = "&".join([f"{k}={str(v)}" for k, v in params.items()])
        url = f"https://minico.qq.com/minico/cgiproxy/v3_release/v3/getillegalityhistory?{param_str}"
        
        logger.debug(f"查询 URL: {url}")
        
        body = {
            "com": {
                "src": 0,
                "scene": 1001,
                "platform": 2,
                "version": "8.9.85.12820"
            },
            "pageNum": 0,
            "pageSize": num
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers)
            result = response.json()
            
            # logger.debug(f"查询违规记录响应: {result}")
            
            return result
    
    def format_violation_record(self, records: list) -> str:
        """格式化违规记录输出"""
        if not records:
            return "未查询到违规记录。"
        
        output = [f"查询到 {len(records)} 条违规记录：\n"]
        
        for i, record in enumerate(records, 1):
            reason_raw = record.get("reason", 999)
            try:
                reason_code = int(reason_raw)
            except Exception:
                reason_code = 999

            time_raw = record.get("time", 0)
            try:
                violation_time = int(time_raw)
            except Exception:
                violation_time = 0

            violation_info = None
            for key, value in violationdata.items():
                if value.get("reason") == reason_code:
                    violation_info = value
                    break
            
            if not violation_info:
                violation_info = violationdata.get("LOCKTOWER_REASON_SMART_OTHER", {})
            
            time_str = (
                datetime.fromtimestamp(violation_time).strftime("%Y-%m-%d %H:%M:%S")
                if violation_time else "未知"
            )
            
            output.append(f"【违规 {i}】")
            output.append(f"时间: {time_str}")
            output.append(f"原因: {violation_info.get('reasonDesc', '未知')}")
            output.append(f"描述: {violation_info.get('description', '无')}")
            output.append("")
        
        return "\n".join(output)
    
    def generate_qrcode(self, data: str) -> bytes:
        """生成二维码图片"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    @filter.command("查违规", alias=['违规查询', '我的违规'])
    async def query_violation(self, event: AstrMessageEvent):
        """查询QQ违规记录"""
        try:
            yield event.plain_result("正在生成授权登录链接，请稍候...")
            
            logincode = await self.get_login_code()
            logger.info(f"获取到 logincode: {logincode}")
            
            auth_url = f"https://h5.qzone.qq.com/qqq/code/{logincode}?_proxy=1&from=ide"
            qr_image_bytes = self.generate_qrcode(auth_url)
            
            qr_image = Image.fromBytes(qr_image_bytes)
            yield event.chain_result([qr_image])
            yield event.plain_result(f"请在一分钟内通过以下方式授权登录：\n\n1. 扫描上方二维码\n2. 或访问链接：\n{auth_url}\n\n等待授权中... (60秒超时)")
            
            # 轮询扫码状态
            max_attempts = 60 
            ticket = None
            
            for i in range(max_attempts):
                await asyncio.sleep(1)
                
                try:
                    success, ticket_value = await self.check_login_code(logincode)
                    
                    if success and ticket_value:
                        ticket = ticket_value
                        logger.info(f"授权成功，获取到 ticket")
                        yield event.plain_result("授权成功！正在查询违规记录...")
                        break
                except Exception as e:
                    logger.debug(f"轮询检查: {e}")
                    continue
            
            if not ticket:
                yield event.plain_result("授权超时，请重新尝试。")
                return
            
            # 用 ticket 换取 code
            code = await self.get_code_from_ticket(ticket)
            logger.info(f"获取到 code")
            
            # 用 code 换取认证信息
            auth_data = await self.get_token_from_code(code)
            logger.info(f"获取到认证信息")
            
            # 查询违规记录
            result = await self.get_record(auth_data)
            
            # 检查返回结果
            ret_code = result.get("retcode")
            if ret_code is None:
                ret_code = result.get("ret")
            error_msg = result.get("message") or result.get("msg", "未知错误")
            
            logger.info(f"查询结果: retcode={ret_code}, totalSize={result.get('totalSize')}")
            
            if ret_code is not None and ret_code != 0:
                yield event.plain_result(f"查询失败 [{ret_code}]: {error_msg}")
                return
            
            # 检查是否有违规记录
            records = result.get("records", [])
            total_size = result.get("totalSize", 0)
            
            if total_size < 1 and not records:
                yield event.plain_result("未查询到违规记录。")
            else:
                formatted_result = self.format_violation_record(records)
                yield event.plain_result(formatted_result)
                
        except Exception as e:
            logger.error(f"查询违规记录失败: {e}", exc_info=True)
            yield event.plain_result(f"查询出错: {str(e)}")
    