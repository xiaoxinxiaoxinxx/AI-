<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="16">
        <div class="panel">
          <div class="panel-title">
            <span>联邦学习训练控制</span>
            <el-tag type="warning" size="small" style="margin-left:10px">数据来源：MySQL数据库</el-tag>
            <el-button type="primary" @click="startTraining" :loading="training" :disabled="training" style="margin-left:auto">
              <el-icon><Cpu /></el-icon> {{ training ? '训练中...' : '开始联邦训练' }}
            </el-button>
          </div>

          <el-alert type="info" :closable="false" style="margin-bottom:16px">
            <template #title>
              💡 点击「开始联邦训练」后，系统将自动从 MySQL 数据库读取所有医院的患者数据，
              各医院在本地训练模型后通过 FedAvg 聚合为全局模型。添加新患者后再训练，模型会学习到新数据。
            </template>
          </el-alert>

          <!-- 联邦学习流程图 -->
          <div class="federated-flow" style="margin-bottom:20px">
            <div class="flow-node">
              <div class="node-icon">🏥</div>
              <div class="node-label">医院A<br/>本地训练</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-node">
              <div class="node-icon">🔄</div>
              <div class="node-label">FedAvg<br/>加权聚合</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-node">
              <div class="node-icon">🧠</div>
              <div class="node-label">全局模型<br/>参数更新</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-node">
              <div class="node-icon">📡</div>
              <div class="node-label">广播<br/>下一轮</div>
            </div>
          </div>

          <!-- 训练进度 -->
          <div v-if="training" class="training-progress">
            <el-progress
              type="circle"
              :percentage="Math.round((currentRound / totalRounds) * 100)"
              :width="160"
              :color="'#1a73e8'"
            >
              <template #default>
                <div style="font-size:14px;color:#666">训练轮次</div>
                <div style="font-size:28px;font-weight:700;color:#1a73e8">{{ currentRound }}/{{ totalRounds }}</div>
              </template>
            </el-progress>
          </div>

          <!-- 实时指标 -->
          <div v-if="currentMetrics" class="training-stats">
            <div class="training-stat">
              <div class="value">{{ (currentMetrics.accuracy * 100).toFixed(1) }}%</div>
              <div class="label">准确率</div>
            </div>
            <div class="training-stat">
              <div class="value">{{ (currentMetrics.precision * 100).toFixed(1) }}%</div>
              <div class="label">精确率</div>
            </div>
            <div class="training-stat">
              <div class="value">{{ (currentMetrics.recall * 100).toFixed(1) }}%</div>
              <div class="label">召回率</div>
            </div>
            <div class="training-stat">
              <div class="value">{{ (currentMetrics.f1 * 100).toFixed(1) }}%</div>
              <div class="label">F1分数</div>
            </div>
          </div>

          <!-- 收敛曲线 -->
          <div v-if="history.length > 0" ref="convergenceRef" style="width:100%;height:350px;margin-top:20px"></div>
        </div>
      </el-col>

      <el-col :span="8">
        <!-- 模型评估 -->
        <div class="panel" v-if="evaluation">
          <div class="panel-title">模型评估报告</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="准确率">
              <span style="font-weight:600;color:#1a73e8">{{ (evaluation.accuracy * 100).toFixed(2) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="精确率">
              <span style="font-weight:600">{{ (evaluation.precision * 100).toFixed(2) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="召回率">
              <span style="font-weight:600">{{ (evaluation.recall * 100).toFixed(2) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="F1分数">
              <span style="font-weight:600;color:#43a047">{{ (evaluation.f1_score * 100).toFixed(2) }}%</span>
            </el-descriptions-item>
            <el-descriptions-item label="测试集大小">{{ evaluation.test_size }} 条</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 隐私保护说明 -->
        <div class="panel">
          <div class="panel-title">🔒 隐私保护要点</div>
          <el-timeline>
            <el-timeline-item>
              <strong>数据保护</strong>：各医院原始数据全程留在各自节点，从不传输
            </el-timeline-item>
            <el-timeline-item>
              <strong>模型聚合</strong>：研究方只收到聚合后的模型参数，无法反推个人数据
            </el-timeline-item>
            <el-timeline-item>
              <strong>FedAvg算法</strong>：使用加权平均聚合各医院模型更新，保护数据隐私
            </el-timeline-item>
            <el-timeline-item>
              <strong>可扩展性</strong>：可进一步叠加差分隐私保护梯度信息
            </el-timeline-item>
          </el-timeline>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { trainModel, getModelEvaluation } from '../api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const training = ref(false)
const currentRound = ref(0)
const totalRounds = ref(10)
const currentMetrics = ref(null)
const history = ref([])
const evaluation = ref(null)
const convergenceRef = ref(null)

watch(history, async () => {
  await nextTick()
  initConvergenceChart()
}, { deep: true })

onMounted(async () => {
  try {
    const res = await getModelEvaluation()
    if (res.code === 200) evaluation.value = res.data
  } catch (e) {}
})

async function startTraining() {
  training.value = true
  currentRound.value = 0
  history.value = []
  currentMetrics.value = null

  try {
    // 模拟训练进度（轮询方式）
    const res = await trainModel()
    if (res.code === 200) {
      history.value = res.data.history
      evaluation.value = res.data.evaluation
      currentRound.value = res.data.history.length
      totalRounds.value = res.data.history.length
      if (res.data.history.length > 0) {
        const last = res.data.history[res.data.history.length - 1]
        currentMetrics.value = {
          accuracy: last.accuracy,
          precision: last.precision,
          recall: last.recall,
          f1: last.f1_score
        }
      }
      ElMessage.success('联邦训练完成！')
    } else {
      ElMessage.error(res.message)
    }
  } catch (e) {
    ElMessage.error('训练失败，请检查后端服务')
  } finally {
    training.value = false
  }
}

function initConvergenceChart() {
  if (!convergenceRef.value || history.value.length === 0) return
  const chart = echarts.init(convergenceRef.value)
  const rounds = history.value.map(h => h.round)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['准确率', '精确率', '召回率', 'F1分数'], bottom: 0 },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: rounds,
      name: '训练轮次'
    },
    yAxis: {
      type: 'value',
      name: '数值',
      min: 0,
      max: 1
    },
    series: [
      {
        name: '准确率', type: 'line', data: history.value.map(h => h.accuracy),
        smooth: true, lineStyle: { width: 3 }, itemStyle: { color: '#1a73e8' }
      },
      {
        name: '精确率', type: 'line', data: history.value.map(h => h.precision),
        smooth: true, itemStyle: { color: '#43a047' }
      },
      {
        name: '召回率', type: 'line', data: history.value.map(h => h.recall),
        smooth: true, itemStyle: { color: '#fb8c00' }
      },
      {
        name: 'F1分数', type: 'line', data: history.value.map(h => h.f1_score),
        smooth: true, lineStyle: { width: 3, type: 'dashed' }, itemStyle: { color: '#8e24aa' }
      }
    ]
  })
}
</script>