<template>
  <div>
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon blue"><el-icon :size="24"><User /></el-icon></div>
        <div class="stat-info">
          <h3>{{ dashboard.total_patients }}</h3>
          <p>患者总数</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red"><el-icon :size="24"><Warning /></el-icon></div>
        <div class="stat-info">
          <h3>{{ dashboard.stroke_patients }}</h3>
          <p>中风患者</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon orange"><el-icon :size="24"><TrendCharts /></el-icon></div>
        <div class="stat-info">
          <h3>{{ dashboard.stroke_rate }}%</h3>
          <p>中风率</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple"><el-icon :size="24"><Cpu /></el-icon></div>
        <div class="stat-info">
          <h3>{{ dashboard.total_predictions }}</h3>
          <p>预测记录</p>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 风险分布图 -->
      <el-col :span="12">
        <div class="panel">
          <div class="panel-title">风险等级分布</div>
          <div ref="riskChartRef" class="chart-box"></div>
        </div>
      </el-col>

      <!-- 系统架构图 -->
      <el-col :span="12">
        <div class="panel">
          <div class="panel-title">联邦学习架构</div>
          <div class="federated-flow">
            <div class="flow-node">
              <div class="node-icon">🏥</div>
              <div class="node-label">医院A<br/>本地数据</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-node">
              <div class="node-icon">🔄</div>
              <div class="node-label">FedAvg<br/>聚合</div>
            </div>
            <div class="flow-arrow">→</div>
            <div class="flow-node">
              <div class="node-icon">🧠</div>
              <div class="node-label">全局模型<br/>中风预测</div>
            </div>
          </div>
          <div style="display:flex;justify-content:space-around;margin-top:16px">
            <div class="flow-node">
              <div class="node-icon">🏥</div>
              <div class="node-label">医院B<br/>本地数据</div>
            </div>
            <div style="display:flex;align-items:center">
              <el-icon :size="24" color="#1a73e8"><Top /></el-icon>
            </div>
            <div class="flow-node">
              <div class="node-icon">🔒</div>
              <div class="node-label">隐私保护<br/>数据不出域</div>
            </div>
            <div style="display:flex;align-items:center">
              <el-icon :size="24" color="#1a73e8"><Bottom /></el-icon>
            </div>
            <div class="flow-node">
              <div class="node-icon">🏥</div>
              <div class="node-label">医院C<br/>本地数据</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 最近预测 -->
    <div class="panel">
      <div class="panel-title">最近预测记录</div>
      <el-table :data="dashboard.recent_predictions" stripe style="width:100%">
        <el-table-column prop="patient_name" label="患者" width="100" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="age" label="年龄" width="60" />
        <el-table-column prop="stroke_probability" label="中风概率" width="100">
          <template #default="{ row }">
            <span style="font-weight:600">{{ (row.stroke_probability * 100).toFixed(1) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <span :class="`risk-${row.risk_level === '高风险' ? 'high' : row.risk_level === '中风险' ? 'medium' : 'low'}`">
              {{ row.risk_level }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="预测时间" min-width="160" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { getDashboard } from '../api'
import * as echarts from 'echarts'

const dashboard = reactive({
  total_patients: 0,
  stroke_patients: 0,
  stroke_rate: 0,
  total_predictions: 0,
  risk_distribution: {},
  recent_predictions: [],
  train_history: []
})

const riskChartRef = ref(null)

onMounted(async () => {
  try {
    const res = await getDashboard()
    if (res.code === 200) {
      Object.assign(dashboard, res.data)
    }
  } catch (e) {}
  await nextTick()
  initRiskChart()
})

function initRiskChart() {
  if (!riskChartRef.value) return
  const chart = echarts.init(riskChartRef.value)
  const dist = dashboard.risk_distribution || {}
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '45%'],
      label: { show: true, formatter: '{b}\n{d}%' },
      data: [
        { value: dist['低风险'] || 0, name: '低风险', itemStyle: { color: '#43a047' } },
        { value: dist['中风险'] || 0, name: '中风险', itemStyle: { color: '#fb8c00' } },
        { value: dist['高风险'] || 0, name: '高风险', itemStyle: { color: '#e53935' } }
      ]
    }]
  })
}
</script>