<template>
  <div>
    <el-row :gutter="20">
      <!-- 预测表单 -->
      <el-col :span="10">
        <div class="panel">
          <div class="panel-title">中风风险评估</div>
          <el-form :model="form" label-width="85px">
            <el-form-item label="患者">
              <el-select v-model="selectedPatientId" placeholder="选择已有患者" filterable clearable @change="onPatientSelect" style="width:100%">
                <el-option v-for="p in patients" :key="p.id" :label="`${p.name} (${p.gender}, ${p.age}岁)`" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="性别">
                  <el-select v-model="form.gender" style="width:100%">
                    <el-option label="男性" value="男性" />
                    <el-option label="女性" value="女性" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="年龄">
                  <el-input-number v-model="form.age" :min="0" :max="120" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="高血压">
                  <el-switch v-model="form.hypertension" :active-value="1" :inactive-value="0" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="心脏病">
                  <el-switch v-model="form.heart_disease" :active-value="1" :inactive-value="0" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="婚姻">
                  <el-switch v-model="form.married" :active-value="1" :inactive-value="0" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="工作类型">
                  <el-select v-model="form.work_type" style="width:100%">
                    <el-option label="私人企业" value="私人企业" />
                    <el-option label="自雇人士" value="自雇人士" />
                    <el-option label="政府工作" value="政府工作" />
                    <el-option label="无业" value="无业" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="住宅类型">
                  <el-select v-model="form.residence_type" style="width:100%">
                    <el-option label="城市" value="城市" />
                    <el-option label="农村" value="农村" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="吸烟状况">
                  <el-select v-model="form.smoking_status" style="width:100%">
                    <el-option label="从不吸烟" value="从不吸烟" />
                    <el-option label="以前吸烟" value="以前吸烟" />
                    <el-option label="吸烟" value="吸烟" />
                    <el-option label="不详" value="不详" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="血糖水平">
                  <el-input-number v-model="form.glucose_level" :precision="2" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="BMI">
                  <el-input-number v-model="form.bmi" :precision="1" :step="0.1" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <el-button type="primary" size="large" style="width:100%" @click="handlePredict" :loading="predicting">
                <el-icon><Search /></el-icon> 开始评估中风风险
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 预测结果 -->
      <el-col :span="14">
        <div class="panel" v-if="result">
          <div class="panel-title">预测结果</div>
          <div style="display:flex;align-items:center;gap:40px;padding:20px 0">
            <!-- 风险仪表盘 -->
            <div ref="gaugeRef" style="width:260px;height:220px"></div>
            <div>
              <div style="font-size:14px;color:#999;margin-bottom:8px">中风风险概率</div>
              <div style="font-size:48px;font-weight:700" :style="{ color: riskColor }">
                {{ (result.probability * 100).toFixed(2) }}%
              </div>
              <div style="margin-top:8px">
                <span :class="`risk-${result.risk_level === '高风险' ? 'high' : result.risk_level === '中风险' ? 'medium' : 'low'}`" style="font-size:16px;padding:4px 16px">
                  {{ result.risk_level }}
                </span>
              </div>
              <div style="margin-top:16px;font-size:12px;color:#999">
                不中风的概率：{{ (result.no_stroke_prob * 100).toFixed(2) }}%
              </div>
            </div>
          </div>
          <el-divider />
          <div style="font-size:13px;color:#666">
            💡 <strong>建议：</strong>
            <span v-if="result.risk_level === '高风险'">
              该患者中风风险较高，建议立即进行进一步检查，控制血压血糖，改善生活方式。
            </span>
            <span v-else-if="result.risk_level === '中风险'">
              该患者存在一定中风风险，建议定期体检，关注血压和血糖指标，保持健康饮食。
            </span>
            <span v-else>
              该患者当前中风风险较低，建议保持健康生活方式，定期体检。
            </span>
          </div>
        </div>

        <!-- 无结果时显示提示 -->
        <div class="panel" v-else>
          <div class="panel-title">预测结果</div>
          <div style="text-align:center;padding:60px 0;color:#bbb">
            <el-icon :size="48"><Warning /></el-icon>
            <p style="margin-top:12px">请选择患者或填写信息后点击"开始评估"</p>
          </div>
        </div>

        <!-- 预测历史 -->
        <div class="panel" v-if="predictions.length > 0">
          <div class="panel-title">预测历史</div>
          <el-table :data="predictions" stripe size="small">
            <el-table-column prop="patient_name" label="患者" width="100" />
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
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getPatients, getPatient, predictStroke, getPredictions } from '../api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const route = useRoute()
const patients = ref([])
const predictions = ref([])
const predicting = ref(false)
const result = ref(null)
const gaugeRef = ref(null)
const selectedPatientId = ref(null)

const form = reactive({
  patient_id: null,
  gender: '男性',
  age: 60,
  hypertension: 0,
  heart_disease: 0,
  married: 0,
  work_type: '私人企业',
  residence_type: '城市',
  glucose_level: 100,
  bmi: 25,
  smoking_status: '从不吸烟'
})

const riskColor = computed(() => {
  if (!result.value) return '#333'
  if (result.value.risk_level === '高风险') return '#e53935'
  if (result.value.risk_level === '中风险') return '#fb8c00'
  return '#43a047'
})

watch(result, async (val) => {
  if (val) {
    await nextTick()
    initGauge()
  }
})

onMounted(async () => {
  try {
    const res = await getPatients({ page: 1, page_size: 1000 })
    if (res.code === 200) patients.value = res.data.list
  } catch (e) {}
  loadPredictions()

  // 如果从患者列表跳转过来
  if (route.query.patient_id) {
    selectedPatientId.value = parseInt(route.query.patient_id)
    onPatientSelect(route.query.patient_id)
  }
})

async function onPatientSelect(pid) {
  if (!pid) return
  try {
    const res = await getPatient(pid)
    if (res.code === 200) {
      const p = res.data
      form.patient_id = p.id
      form.gender = p.gender
      form.age = p.age
      form.hypertension = p.hypertension
      form.heart_disease = p.heart_disease
      form.married = p.married
      form.work_type = p.work_type
      form.residence_type = p.residence_type
      form.glucose_level = p.glucose_level
      form.bmi = p.bmi
      form.smoking_status = p.smoking_status
    }
  } catch (e) {}
}

async function handlePredict() {
  predicting.value = true
  try {
    const res = await predictStroke({
      patient_id: form.patient_id,
      ...form
    })
    if (res.code === 200) {
      result.value = res.data
      ElMessage.success('预测完成')
      loadPredictions()
    } else {
      ElMessage.error(res.message || '预测失败')
    }
  } catch (e) {
    ElMessage.error('预测失败，请先完成联邦训练')
  } finally {
    predicting.value = false
  }
}

async function loadPredictions() {
  try {
    const res = await getPredictions({ page: 1, page_size: 5 })
    if (res.code === 200) predictions.value = res.data.list
  } catch (e) {}
}

function initGauge() {
  if (!gaugeRef.value) return
  const chart = echarts.init(gaugeRef.value)
  const prob = (result.value.probability * 100).toFixed(1)
  chart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 210,
      endAngle: -30,
      center: ['50%', '55%'],
      radius: '90%',
      min: 0,
      max: 100,
      axisLine: {
        lineStyle: {
          width: 16,
          color: [
            [0.3, '#43a047'],
            [0.6, '#fb8c00'],
            [1, '#e53935']
          ]
        }
      },
      pointer: { length: '60%', width: 6 },
      axisTick: { distance: -12, length: 6 },
      splitLine: { distance: -18, length: 14 },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        fontSize: 20,
        offsetCenter: [0, '70%']
      },
      data: [{ value: parseFloat(prob) }]
    }]
  })
}
</script>