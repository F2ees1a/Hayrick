<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo-section">
          <el-icon class="logo-icon" :size="32"><Crop /></el-icon>
          <div class="title-section">
            <h1 class="title">农田草垛视觉识别系统</h1>
            <p class="subtitle">AgriVision Haystack Detector</p>
          </div>
        </div>
        <div class="status-section">
          <el-tag :type="modelStatus === 'ready' ? 'success' : 'warning'" size="large">
            <el-icon v-if="modelStatus === 'ready'"><CircleCheck /></el-icon>
            <el-icon v-else><Loading /></el-icon>
            {{ modelStatus === 'ready' ? '模型已就绪' : '模型加载中' }}
          </el-tag>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <el-row :gutter="24">
        <!-- 左侧：上传和控制区 -->
        <el-col :xs="24" :lg="8">
          <el-card class="upload-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span><el-icon><Upload /></el-icon> 图片上传</span>
              </div>
            </template>

            <!-- 上传模式选择 -->
            <el-radio-group v-model="uploadMode" class="mode-select" @change="handleModeChange">
              <el-radio-button value="single">
                <el-icon><Picture /></el-icon> 单张图片
              </el-radio-button>
              <el-radio-button value="multiple">
                <el-icon><Folder /></el-icon> 多张图片
              </el-radio-button>
            </el-radio-group>

            <!-- 单张图片上传 -->
            <div v-if="uploadMode === 'single'" class="upload-section">
              <el-upload
                ref="singleUploadRef"
                class="single-uploader"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleSingleFileChange"
                accept="image/*"
                :limit="1"
              >
                <div class="upload-trigger" v-if="!previewImage">
                  <el-icon class="upload-icon"><Plus /></el-icon>
                  <div class="upload-text">点击上传图片</div>
                  <div class="upload-hint">支持 JPG, PNG, JPEG 格式</div>
                </div>
                <img v-else :src="previewImage" class="preview-image" />
              </el-upload>
              <el-button v-if="previewImage" text @click="clearSingleImage">
                <el-icon><Delete /></el-icon> 清除图片
              </el-button>
            </div>

            <!-- 多张图片上传 -->
            <div v-else class="upload-section">
              <el-upload
                ref="multiUploadRef"
                class="multi-uploader"
                :auto-upload="false"
                :show-file-list="true"
                :file-list="fileList"
                :on-change="handleMultiFileChange"
                :on-remove="handleMultiFileRemove"
                accept="image/*"
                multiple
                drag
              >
                <div class="upload-trigger">
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">将图片拖到此处，或<em>点击上传</em></div>
                  <div class="upload-hint">支持批量上传多张图片</div>
                </div>
              </el-upload>
              <div class="file-count" v-if="fileList.length > 0">
                已选择 {{ fileList.length }} 张图片
              </div>
            </div>

            <!-- 参数设置 -->
            <div class="settings-section">
              <h4><el-icon><Setting /></el-icon> 参数设置</h4>
              
              <div class="setting-item">
                <label>置信度阈值:</label>
                <el-slider 
                  v-model="confidence" 
                  :min="0.1" 
                  :max="1" 
                  :step="0.05"
                  :format-tooltip="(val) => `${Math.round(val * 100)}%`"
                />
                <span class="confidence-value">{{ Math.round(confidence * 100) }}%</span>
              </div>

              <div class="setting-item">
                <label>保存结果:</label>
                <el-switch v-model="saveResults" />
              </div>

              <div class="setting-item" v-if="saveResults">
                <label>保存路径:</label>
                <el-input 
                  v-model="savePath" 
                  placeholder="输入保存路径 (如: D:/results)"
                >
                  <template #append>
                    <el-button @click="selectSavePath">
                      <el-icon><FolderOpened /></el-icon>
                    </el-button>
                  </template>
                </el-input>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button 
                type="primary" 
                size="large" 
                :loading="isProcessing"
                :disabled="!canStartDetection"
                @click="startDetection"
              >
                <el-icon v-if="!isProcessing"><CaretRight /></el-icon>
                {{ isProcessing ? '处理中...' : '开始检测' }}
              </el-button>
              <el-button 
                size="large" 
                :disabled="results.length === 0"
                @click="resetAll"
              >
                <el-icon><RefreshRight /></el-icon>
                重置
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：结果展示区 -->
        <el-col :xs="24" :lg="16">
          <el-card class="result-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span><el-icon><PictureFilled /></el-icon> 检测结果</span>
                <div class="result-stats" v-if="results.length > 0">
                  <el-tag type="success">已处理: {{ results.length }}</el-tag>
                  <el-tag type="warning">检测到: {{ totalDetections }} 个</el-tag>
                </div>
              </div>
            </template>

            <!-- 结果展示 -->
            <div class="results-container" v-if="results.length > 0">
              <div class="results-grid">
                <div 
                  v-for="(result, index) in results" 
                  :key="result.image_id"
                  class="result-item"
                  :class="{ 'selected': selectedImages.includes(result.image_id) }"
                  @click="toggleImageSelection(result.image_id)"
                >
                  <div class="result-image-wrapper">
                    <img 
                      :src="'data:image/jpeg;base64,' + result.processed_image" 
                      class="result-image"
                    />
                    <div class="result-overlay">
                      <el-tag 
                        :type="result.detected ? 'success' : 'info'" 
                        size="small"
                      >
                        {{ result.detected ? `检测到 ${result.detections} 个` : '未检测到' }}
                      </el-tag>
                    </div>
                    <div class="result-checkbox" v-if="result.detected">
                      <el-checkbox 
                        :model-value="selectedImages.includes(result.image_id)"
                        @click.stop
                        @change="toggleImageSelection(result.image_id)"
                      />
                    </div>
                  </div>
                  <div class="result-info">
                    <span class="filename" :title="result.original_filename">
                      {{ result.original_filename }}
                    </span>
                    <span class="confidence" v-if="result.detected">
                      置信度: {{ (result.confidence * 100).toFixed(1) }}%
                    </span>
                  </div>
                  <div class="result-actions">
                    <el-button 
                      size="small" 
                      type="primary"
                      text
                      @click.stop="downloadImage(result)"
                    >
                      <el-icon><Download /></el-icon> 下载
                    </el-button>
                  </div>
                </div>
              </div>

              <!-- 批量操作 -->
              <div class="batch-actions" v-if="selectedImages.length > 0">
                <el-divider />
                <div class="batch-content">
                  <span>已选择 {{ selectedImages.length }} 张图片</span>
                  <div class="batch-buttons">
                    <el-button type="success" @click="downloadSelected">
                      <el-icon><Download /></el-icon> 下载选中
                    </el-button>
                    <el-button 
                      type="primary" 
                      @click="showSaveDialog"
                      v-if="!saveResults"
                    >
                      <el-icon><FolderAdd /></el-icon> 保存选中到指定位置
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div class="empty-state" v-else>
              <el-icon :size="80" color="#ccc"><PictureFilled /></el-icon>
              <p>暂无检测结果</p>
              <p class="empty-hint">请先上传图片开始检测</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </main>

    <!-- 保存对话框 -->
    <el-dialog 
      v-model="saveDialogVisible" 
      title="保存选中图片" 
      width="500px"
    >
      <el-form label-width="80px">
        <el-form-item label="保存路径">
          <el-input v-model="dialogSavePath" placeholder="请输入保存路径">
            <template #append>
              <el-button @click="selectDialogSavePath">
                <el-icon><FolderOpened /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSelectedImages">确认保存</el-button>
      </template>
    </el-dialog>

    <!-- 页脚 -->
    <footer class="footer">
      <p>© 2024 农田草垛视觉识别系统 | 基于 YOLOv5 模型</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// API基础URL
const API_BASE = '/api'

// 响应式状态
const uploadMode = ref('single')
const previewImage = ref(null)
const fileList = ref([])
const confidence = ref(0.25)
const saveResults = ref(false)
const savePath = ref('')
const isProcessing = ref(false)
const results = ref([])
const selectedImages = ref([])
const modelStatus = ref('loading')

// 对话框状态
const saveDialogVisible = ref(false)
const dialogSavePath = ref('')

// 计算属性
const canStartDetection = computed(() => {
  if (uploadMode.value === 'single') {
    return previewImage.value !== null
  } else {
    return fileList.value.length > 0
  }
})

const totalDetections = computed(() => {
  return results.value.reduce((sum, r) => sum + r.detections, 0)
})

// 检查模型状态
const checkModelStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE}/health`)
    modelStatus.value = response.data.model_loaded ? 'ready' : 'loading'
  } catch (error) {
    console.error('模型状态检查失败:', error)
    modelStatus.value = 'error'
  }
}

// 处理模式切换
const handleModeChange = () => {
  clearAllFiles()
}

// 清除单张图片
const clearSingleImage = () => {
  previewImage.value = null
  if (singleUploadRef.value) {
    singleUploadRef.value.clearFiles()
  }
}

// 清除所有文件
const clearAllFiles = () => {
  previewImage.value = null
  fileList.value = []
  if (singleUploadRef.value) {
    singleUploadRef.value.clearFiles()
  }
  if (multiUploadRef.value) {
    multiUploadRef.value.clearFiles()
  }
}

// 处理单张文件选择
const handleSingleFileChange = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    previewImage.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

// 处理多文件选择
const handleMultiFileChange = (file, files) => {
  fileList.value = files
}

// 处理多文件移除
const handleMultiFileRemove = (file, files) => {
  fileList.value = files
}

// 选择保存路径
const selectSavePath = () => {
  // 由于浏览器安全限制，这里让用户手动输入路径
  ElMessage.info('请在下方输入框中输入保存路径')
}

// 选择对话框中的保存路径
const selectDialogSavePath = () => {
  ElMessage.info('请在输入框中输入保存路径')
}

// 开始检测
const startDetection = async () => {

  isProcessing.value = true
  results.value = []

  try {

    const formData = new FormData()

    if (uploadMode.value === 'single') {

      const response = await fetch(previewImage.value)
      const blob = await response.blob()

      formData.append('files', blob, "image.jpg")

    } else {

      for (const file of fileList.value) {
        formData.append('files', file.raw)
      }

    }

    formData.append('confidence', confidence.value)

    const response = await axios.post(`${API_BASE}/detect`, formData)

    results.value = response.data.results

    ElMessage.success(response.data.message)

  } catch (err) {

    console.error(err)

    ElMessage.error("检测失败")

  }

  isProcessing.value = false
}

// 切换图片选中状态
const toggleImageSelection = (imageId) => {
  const index = selectedImages.value.indexOf(imageId)
  if (index > -1) {
    selectedImages.value.splice(index, 1)
  } else {
    selectedImages.value.push(imageId)
  }
}

// 下载单张图片
const downloadImage = (result) => {
  const link = document.createElement('a')
  link.href = `data:image/jpeg;base64,${result.processed_image}`
  link.download = `detected_${result.original_filename}`
  link.click()
}

// 下载选中的图片
const downloadSelected = () => {
  const selectedResults = results.value.filter(
    r => selectedImages.value.includes(r.image_id)
  )
  
  for (const result of selectedResults) {
    downloadImage(result)
  }
  
  ElMessage.success(`已下载 ${selectedResults.length} 张图片`)
}

// 显示保存对话框
const showSaveDialog = () => {
  dialogSavePath.value = savePath.value
  saveDialogVisible.value = true
}

// 保存选中的图片到指定位置
const saveSelectedImages = async () => {
  if (!dialogSavePath.value) {
    ElMessage.warning('请输入保存路径')
    return
  }

  const selectedResults = results.value.filter(
    r => selectedImages.value.includes(r.image_id)
  )

  const images = selectedResults.map(r => r.processed_image)
  const filenames = selectedResults.map(r => r.original_filename)

  try {
    const response = await axios.post(`${API_BASE}/save-selected`, {
      images: images,
      save_path: dialogSavePath.value,
      filenames: filenames
    })

    if (response.data.success) {
      ElMessage.success(response.data.message)
      saveDialogVisible.value = false
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，请检查路径是否正确')
  }
}

// 重置所有
const resetAll = () => {
  ElMessageBox.confirm('确定要重置所有内容吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    clearAllFiles()
    results.value = []
    selectedImages.value = []
  }).catch(() => {})
}

// 生命周期钩子
onMounted(() => {
  checkModelStatus()
  // 定期检查模型状态
  setInterval(checkModelStatus, 30000)
})

// 模板引用
const singleUploadRef = ref(null)
const multiUploadRef = ref(null)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  padding-bottom: 60px;
}

/* 头部样式 */
.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  color: #2E7D32;
}

.title-section .title {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
  line-height: 1.2;
}

.title-section .subtitle {
  font-size: 12px;
  color: #666;
  margin: 0;
}

/* 主内容区 */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* 卡片样式 */
.upload-card,
.result-card {
  border-radius: 16px;
  overflow: hidden;
}

.upload-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.card-header .el-icon {
  margin-right: 8px;
}

.result-stats {
  display: flex;
  gap: 8px;
}

/* 上传区域 */
.mode-select {
  width: 100%;
  margin-bottom: 20px;
}

.mode-select .el-radio-button {
  width: 50%;
}

.mode-select .el-radio-button__inner {
  width: 100%;
}

.upload-section {
  margin: 20px 0;
}

.single-uploader {
  width: 100%;
}

.upload-trigger {
  width: 100%;
  padding: 40px 20px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}

.upload-trigger:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-icon {
  font-size: 48px;
  color: #909399;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.preview-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
}

.file-count {
  margin-top: 12px;
  font-size: 14px;
  color: #409eff;
  text-align: center;
}

/* 设置区域 */
.settings-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.settings-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #303133;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.setting-item label {
  min-width: 80px;
  font-size: 14px;
  color: #606266;
}

.setting-item .el-slider {
  flex: 1;
}

.confidence-value {
  min-width: 50px;
  text-align: right;
  font-size: 14px;
  color: #409eff;
  font-weight: 600;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.action-buttons .el-button {
  flex: 1;
}

/* 结果展示 */
.results-container {
  min-height: 400px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.result-item {
  border: 2px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
}

.result-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.result-image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
  background: #f5f7fa;
  overflow: hidden;
}

.result-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.result-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
}

.result-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
}

.result-info {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-info .filename {
  font-size: 13px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-info .confidence {
  font-size: 12px;
  color: #909399;
}

.result-actions {
  padding: 0 12px 12px;
  display: flex;
  justify-content: flex-end;
}

/* 批量操作 */
.batch-actions {
  margin-top: 20px;
}

.batch-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.batch-buttons {
  display: flex;
  gap: 12px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #909399;
}

.empty-state p {
  margin-top: 16px;
  font-size: 16px;
}

.empty-hint {
  font-size: 14px !important;
  color: #c0c4cc !important;
}

/* 页脚 */
.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  text-align: center;
  padding: 16px;
  font-size: 13px;
  color: #666;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.05);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }

  .batch-content {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
