import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { showAlert } from '@/components/AlertDialog';

interface DebateMessage {
  role: 'plaintiff' | 'defendant' | 'judge';
  content: string;
}

interface CaseInfo {
  case_title: string;
  case_description: string;
  case_type: string;
  debate_turns: DebateMessage[];
  verdict?: string;
}

// 从文本中提取信息的辅助函数
const extractInfo = (text: string, keywords: string[]): string => {
  for (const keyword of keywords) {
    const regex = new RegExp(`${keyword}[:：]\\s*([^，。；\n]+)`, 'i');
    const match = text.match(regex);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  return '';
};

// 从辩论内容和案情描述中提取原告和被告信息
const extractPartyInfo = (debateTurns: DebateMessage[], caseDescription: string = '') => {
  const plaintiffMessages = debateTurns.filter(msg => msg.role === 'plaintiff').map(msg => msg.content).join(' ');
  const defendantMessages = debateTurns.filter(msg => msg.role === 'defendant').map(msg => msg.content).join(' ');
  const allMessages = debateTurns.map(msg => msg.content).join(' ') + ' ' + caseDescription;
  
  // 提取原告信息
  const plaintiffInfo = {
    name: extractInfo(plaintiffMessages, ['原告', '我叫', '本人', '申请人']) || 
          extractInfo(allMessages, ['原告是', '原告为', '原告姓名']) || 
          '未提及',
    gender: extractInfo(plaintiffMessages, ['性别', '男', '女']) || '未提及',
    ethnicity: extractInfo(plaintiffMessages, ['民族']) || '未提及',
    birthDate: extractInfo(plaintiffMessages, ['出生日期', '出生', '生于']) || '未提及',
    address: extractInfo(plaintiffMessages, ['住址', '地址', '居住', '住在']) || 
             extractInfo(allMessages, ['原告住址', '原告地址']) || 
             '未提及',
    phone: extractInfo(plaintiffMessages, ['联系电话', '电话', '手机']) || '未提及'
  };
  
  // 提取被告信息
  const defendantInfo = {
    name: extractInfo(defendantMessages, ['被告', '被申请人']) || 
          extractInfo(allMessages, ['被告是', '被告为', '被告姓名', '被告叫']) || 
          '未提及',
    gender: extractInfo(defendantMessages, ['性别', '男', '女']) || '未提及',
    ethnicity: extractInfo(defendantMessages, ['民族']) || '未提及',
    birthDate: extractInfo(defendantMessages, ['出生日期', '出生', '生于']) || '未提及',
    address: extractInfo(defendantMessages, ['住址', '地址', '居住', '住在']) || 
             extractInfo(allMessages, ['被告住址', '被告地址']) || 
             '未提及',
    phone: extractInfo(defendantMessages, ['联系电话', '电话', '手机']) || '未提及'
  };
  
  // 提取诉讼请求
  const claims: string[] = [];
  const claimPatterns = [
    /请求[:：]\s*([^。；\n]+)/gi,
    /要求[:：]\s*([^。；\n]+)/gi,
    /判令[:：]\s*([^。；\n]+)/gi,
    /主张[:：]\s*([^。；\n]+)/gi
  ];
  
  for (const pattern of claimPatterns) {
    let match;
    while ((match = pattern.exec(allMessages)) !== null) {
      if (match[1] && match[1].trim().length > 5) {
        claims.push(match[1].trim());
      }
    }
  }
  
  // 提取证据
  const evidence: string[] = [];
  const evidencePatterns = [
    /证据[:：]\s*([^。；\n]+)/gi,
    /提交[:：]\s*([^。；\n]+)/gi,
    /出示[:：]\s*([^。；\n]+)/gi
  ];
  
  for (const pattern of evidencePatterns) {
    let match;
    while ((match = pattern.exec(allMessages)) !== null) {
      if (match[1] && match[1].trim().length > 3) {
        evidence.push(match[1].trim());
      }
    }
  }
  
  return { plaintiffInfo, defendantInfo, claims, evidence };
};

export const generateComplaintPDF = async (caseInfo: CaseInfo) => {
  // 提取信息
  const { plaintiffInfo, defendantInfo, claims, evidence } = extractPartyInfo(caseInfo.debate_turns, caseInfo.case_description);
  
  // 创建一个临时的HTML元素来生成PDF
  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.left = '-9999px';
  container.style.top = '-9999px';
  container.style.width = '210mm';
  container.style.minHeight = '297mm';
  container.style.padding = '20mm';
  container.style.fontFamily = 'SimSun, serif';
  container.style.fontSize = '12px';
  container.style.lineHeight = '1.5';
  container.style.whiteSpace = 'normal';
  container.style.wordWrap = 'break-word';
  container.style.backgroundColor = 'white';
  
  // 构建起诉状HTML内容
  const htmlContent = `
    <div style="font-family: SimSun, serif; line-height: 1.5;">
      <h1 style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 20px;">民事起诉状</h1>
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">一、原告信息</h2>
      <p>姓名：${plaintiffInfo.name}</p>
      <p>性别：${plaintiffInfo.gender}</p>
      <p>民族：${plaintiffInfo.ethnicity}</p>
      <p>出生日期：${plaintiffInfo.birthDate}</p>
      <p>住址：${plaintiffInfo.address}</p>
      <p>联系电话：${plaintiffInfo.phone}</p>
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">二、被告信息</h2>
      <p>姓名：${defendantInfo.name}</p>
      <p>性别：${defendantInfo.gender}</p>
      <p>民族：${defendantInfo.ethnicity}</p>
      <p>出生日期：${defendantInfo.birthDate}</p>
      <p>住址：${defendantInfo.address}</p>
      <p>联系电话：${defendantInfo.phone}</p>
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">三、诉讼请求</h2>
      ${claims.length > 0 ? 
        claims.slice(0, 5).map((claim, index) => `<p>${index + 1}. ${claim}</p>`).join('') :
        '<p>1. [根据案件情况填写具体诉讼请求]</p><p>2. [如有多个请求请继续添加]</p>'
      }
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">四、事实与理由</h2>
      <p style="font-weight: bold;">案件基本情况：</p>
      <p style="text-indent: 2em; margin-bottom: 10px;">${caseInfo.case_description || '请根据实际情况填写案件详情'}</p>
      
      ${caseInfo.debate_turns.filter(msg => msg.role === 'plaintiff').length > 0 ? `
        <p style="font-weight: bold; margin-top: 10px;">原告观点及主张：</p>
        ${caseInfo.debate_turns.filter(msg => msg.role === 'plaintiff').slice(0, 3).map((msg, index) => `
          <p style="text-indent: 2em; margin-bottom: 5px;">${index + 1}. ${msg.content}</p>
        `).join('')}
      ` : ''}
      
      ${caseInfo.debate_turns.filter(msg => msg.role === 'defendant').length > 0 ? `
        <p style="font-weight: bold; margin-top: 10px;">被告答辩意见：</p>
        ${caseInfo.debate_turns.filter(msg => msg.role === 'defendant').slice(0, 3).map((msg, index) => `
          <p style="text-indent: 2em; margin-bottom: 5px;">${index + 1}. ${msg.content}</p>
        `).join('')}
      ` : ''}
      
      ${caseInfo.debate_turns.filter(msg => msg.role === 'judge').length > 0 ? `
        <p style="font-weight: bold; margin-top: 10px;">争议焦点及法官意见：</p>
        ${caseInfo.debate_turns.filter(msg => msg.role === 'judge').slice(0, 2).map((msg, index) => `
          <p style="text-indent: 2em; margin-bottom: 5px;">${index + 1}. ${msg.content}</p>
        `).join('')}
      ` : ''}
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">五、法律依据</h2>
      <p style="text-indent: 2em;">根据《中华人民共和国民法典》、《中华人民共和国民事诉讼法》等相关法律法规，原告认为被告的行为已构成侵权/违约，应当承担相应的法律责任。</p>
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">六、证据清单</h2>
      ${evidence.length > 0 ?
        evidence.slice(0, 5).map((item, index) => `<p>${index + 1}. ${item}</p>`).join('') :
        '<p>1. [证据1：如合同、协议等]</p><p>2. [证据2：如聊天记录、转账凭证等]</p><p>3. [证据3：如证人证言、鉴定意见等]</p>'
      }
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">七、此致</h2>
      <p>此致</p>
      <p style="font-weight: bold; margin-left: 2em;">${caseInfo.case_type || 'XXX'}人民法院</p>
      
      <p style="font-weight: bold; margin-top: 20px; margin-left: 60%;">具状人：${plaintiffInfo.name !== '未提及' ? plaintiffInfo.name : '____________'}</p>
      <p style="margin-left: 60%;">日期：${new Date().toLocaleDateString('zh-CN')}</p>
      
      <h2 style="font-size: 14px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">八、附件</h2>
      <p>1. 本起诉状副本${defendantInfo.name !== '未提及' ? '1' : 'X'}份</p>
      <p>2. 证据清单及相关证据材料</p>
      <p>3. 原告身份证明材料</p>
    </div>
  `;
  
  container.innerHTML = htmlContent;
  document.body.appendChild(container);
  
  try {
    // 等待DOM渲染完成
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // 获取内容高度
    const contentHeight = container.scrollHeight;
    const pageHeight = 297; // A4纸高度(mm)
    const pageWidth = 210; // A4纸宽度(mm)
    
    // 使用html2canvas将HTML转换为图片
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false,
      windowWidth: container.scrollWidth,
      windowHeight: contentHeight
    });
    
    // 创建PDF
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });
    
    const imgWidth = pageWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    // 计算需要多少页
    const totalPages = Math.ceil(imgHeight / pageHeight);
    
    // 如果内容超过一页，需要分页处理
    if (totalPages > 1) {
      for (let i = 0; i < totalPages; i++) {
        if (i > 0) {
          pdf.addPage();
        }
        
        // 计算每页应该显示的图片部分
        const sourceY = (i * pageHeight * canvas.width) / imgWidth;
        const sourceHeight = Math.min(
          ((pageHeight * canvas.width) / imgWidth),
          canvas.height - sourceY
        );
        
        // 创建临时canvas来截取当前页的内容
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = canvas.width;
        tempCanvas.height = sourceHeight;
        const tempCtx = tempCanvas.getContext('2d');
        
        if (tempCtx) {
          tempCtx.drawImage(
            canvas,
            0, sourceY, canvas.width, sourceHeight,
            0, 0, canvas.width, sourceHeight
          );
          
          const pageImgData = tempCanvas.toDataURL('image/png');
          const pageImgHeight = (sourceHeight * imgWidth) / canvas.width;
          
          pdf.addImage(pageImgData, 'PNG', 0, 0, imgWidth, pageImgHeight);
        }
      }
    } else {
      // 单页内容
      const imgData = canvas.toDataURL('image/png');
      pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, Math.min(imgHeight, pageHeight));
    }
    
    pdf.save(`起诉状_${caseInfo.case_title || '民事案件'}.pdf`);
  } catch (error) {
    console.error('PDF生成失败:', error);
    showAlert('PDF生成失败，请重试', 'error');
  } finally {
    // 清理临时元素
    document.body.removeChild(container);
  }
};