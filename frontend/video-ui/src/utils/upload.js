import SparkMD5 from 'spark-md5';
import axios from 'axios';
import { getToken } from '@/utils/auth';
import service from '@/api/user';

// 默认分片大小：2MB
const DEFAULT_CHUNK_SIZE = 2 * 1024 * 1024;

/**
 * 计算文件的MD5值
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<string>} - 返回文件MD5值
 */
export function calculateFileMD5(file, onProgress) {
  return new Promise((resolve, reject) => {
    const blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;
    const chunkSize = 2097152; // 分块读取，每块2MB
    const chunks = Math.ceil(file.size / chunkSize);
    let currentChunk = 0;
    const spark = new SparkMD5.ArrayBuffer();
    const fileReader = new FileReader();

    fileReader.onload = (e) => {
      spark.append(e.target.result); // 将分片内容添加到spark中
      currentChunk++;

      if (onProgress) {
        onProgress(Math.floor((currentChunk / chunks) * 100));
      }

      if (currentChunk < chunks) {
        loadNext();
      } else {
        const md5 = spark.end();
        resolve(md5);
      }
    };

    fileReader.onerror = (e) => {
      reject(e);
    };

    function loadNext() {
      const start = currentChunk * chunkSize;
      const end = ((start + chunkSize) >= file.size) ? file.size : start + chunkSize;
      fileReader.readAsArrayBuffer(blobSlice.call(file, start, end));
    }

    loadNext();
  });
}

/**
 * 将文件分片
 * @param {File} file - 文件对象
 * @param {number} chunkSize - 分片大小
 * @returns {Array} - 分片数组
 */
export function createFileChunks(file, chunkSize = DEFAULT_CHUNK_SIZE) {
  const chunks = [];
  const totalChunks = Math.ceil(file.size / chunkSize);

  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, file.size);
    const chunk = file.slice(start, end);
    chunks.push({
      index: i,
      chunk,
      start,
      end,
      size: chunk.size,
      total: totalChunks
    });
  }

  return chunks;
}

/**
 * 检查文件是否已经上传过
 * @param {string} fileName - 文件名
 * @param {string} fileMD5 - 文件MD5值
 * @param {number} fileSize - 文件大小
 * @returns {Promise<object>} - 返回检查结果
 */
export async function checkFileExists(fileName, fileMD5, fileSize) {
  try {
    const response = await service({
      url: '/videos/upload/check/',
      method: 'post',
      data: {
        file_name: fileName,
        file_md5: fileMD5,
        file_size: fileSize
      }
    });
    return response;
  } catch (error) {
    console.error('检查文件失败:', error);
    throw error;
  }
}

/**
 * 上传单个分片
 * @param {Blob} chunk - 分片内容
 * @param {string} fileName - 文件名
 * @param {string} fileMD5 - 文件MD5值
 * @param {number} chunkIndex - 分片索引
 * @param {number} totalChunks - 总分片数
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<object>} - 返回上传结果
 */
export async function uploadChunk(chunk, fileName, fileMD5, chunkIndex, totalChunks, onProgress) {
  const formData = new FormData();
  formData.append('chunk', chunk);
  formData.append('file_name', fileName);
  formData.append('file_md5', fileMD5);
  formData.append('chunk_index', chunkIndex);
  formData.append('chunks_total', totalChunks);

  try {
    const response = await service({
      url: '/videos/upload/chunk/',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total > 0) {
          onProgress(Math.floor((progressEvent.loaded * 100) / progressEvent.total));
        }
      }
    });
    return response;
  } catch (error) {
    console.error(`上传分片${chunkIndex}失败:`, error);
    throw error;
  }
}

/**
 * 合并文件分片
 * @param {string} fileName - 文件名
 * @param {string} fileMD5 - 文件MD5值
 * @param {number} fileSize - 文件大小
 * @param {number} totalChunks - 总分片数
 * @returns {Promise<object>} - 返回合并结果
 */
export async function mergeChunks(fileName, fileMD5, fileSize, totalChunks) {
  try {
    const response = await service({
      url: '/videos/upload/merge/',
      method: 'post',
      data: {
        file_name: fileName,
        file_md5: fileMD5,
        file_size: fileSize,
        chunks_total: totalChunks
      }
    });
    return response;
  } catch (error) {
    console.error('合并分片失败:', error);
    throw error;
  }
}

/**
 * 上传整个文件（分片上传、断点续传）
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 总进度回调
 * @returns {Promise<object>} - 返回上传结果
 */
export async function uploadFile(file, onProgress) {
  try {
    // 1. 计算文件MD5
    onProgress && onProgress(0, '计算文件特征...');
    const fileMD5 = await calculateFileMD5(file, (progress) => {
      onProgress && onProgress(progress * 0.2, '计算文件特征...');
    });

    // 2. 检查文件是否已上传，或获取已上传的分片
    onProgress && onProgress(20, '检查文件状态...');
    const checkResult = await checkFileExists(file.name, fileMD5, file.size);
    
    // 如果文件已完全上传，直接返回结果
    if (checkResult.exists && checkResult.video) {
      onProgress && onProgress(100, '文件已上传');
      return checkResult.video;
    }

    // 获取已上传的分片索引
    const uploadedChunks = checkResult.uploaded_chunks || [];
    
    // 3. 创建文件分片
    const chunks = createFileChunks(file);
    
    // 4. 上传所有未上传的分片
    const uploadPromises = [];
    const totalChunks = chunks.length;
    let completedChunks = uploadedChunks.length;
    
    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      
      // 如果分片已上传，跳过
      if (uploadedChunks.includes(chunk.index)) {
        continue;
      }
      
      // 添加分片上传任务
      uploadPromises.push(
        uploadChunk(
          chunk.chunk,
          file.name,
          fileMD5,
          chunk.index,
          totalChunks,
          () => {
            // 每完成一个分片，更新总进度
            completedChunks++;
            
            // 计算总进度：20% MD5计算 + 70% 分片上传 + 10% 合并
            const totalProgressPercent = 20 + (completedChunks / totalChunks) * 70;
            onProgress && onProgress(Math.min(90, totalProgressPercent), '上传中...');
          }
        )
      );
    }
    
    // 等待所有分片上传完成
    if (uploadPromises.length > 0) {
      onProgress && onProgress(90, '上传中...');
      await Promise.all(uploadPromises);
    }
    
    // 5. 合并文件分片
    onProgress && onProgress(95, '处理中...');
    const mergeResult = await mergeChunks(file.name, fileMD5, file.size, totalChunks);
    
    // 6. 上传完成
    onProgress && onProgress(100, '上传完成');
    
    return mergeResult.video;
  } catch (error) {
    console.error('上传文件失败:', error);
    throw error;
  }
}

export default {
  calculateFileMD5,
  createFileChunks,
  checkFileExists,
  uploadChunk,
  mergeChunks,
  uploadFile
}; 