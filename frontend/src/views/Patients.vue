<template>
  <div>
    <div class="panel">
      <div class="panel-title">
        <span>患者列表</span>
        <el-button type="primary" @click="showDialog = true; editMode = false; resetForm()">
          <el-icon><Plus /></el-icon> 添加患者
        </el-button>
      </div>

      <!-- 搜索 -->
      <div style="margin-bottom:16px;display:flex;gap:12px">
        <el-input v-model="keyword" placeholder="按姓名搜索" style="width:220px" clearable @clear="loadData" @keyup.enter="loadData" />
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="patients" stripe style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="60" />
        <el-table-column prop="age" label="年龄" width="60" />
        <el-table-column prop="hypertension" label="高血压" width="80">
          <template #default="{ row }">
            <el-tag :type="row.hypertension ? 'danger' : 'success'" size="small">
              {{ row.hypertension ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="heart_disease" label="心脏病" width="80">
          <template #default="{ row }">
            <el-tag :type="row.heart_disease ? 'danger' : 'success'" size="small">
              {{ row.heart_disease ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="bmi" label="BMI" width="70" />
        <el-table-column prop="glucose_level" label="血糖" width="80" />
        <el-table-column prop="smoking_status" label="吸烟" width="90" />
        <el-table-column prop="stroke" label="中风" width="80">
          <template #default="{ row }">
            <el-tag :type="row.stroke ? 'danger' : 'info'" size="small">
              {{ row.stroke ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="goPredict(row)">预测</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editMode ? '编辑患者' : '添加患者'" width="600px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="form.name" placeholder="患者姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select v-model="form.gender" style="width:100%">
                <el-option label="男性" value="男性" />
                <el-option label="女性" value="女性" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="年龄">
              <el-input-number v-model="form.age" :min="0" :max="120" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="血压">
              <el-switch v-model="form.hypertension" active-text="高血压" inactive-text="正常" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="心脏病">
              <el-switch v-model="form.heart_disease" active-text="有" inactive-text="无" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="婚姻">
              <el-switch v-model="form.married" active-text="已婚" inactive-text="未婚" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
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
          <el-col :span="12">
            <el-form-item label="住宅类型">
              <el-select v-model="form.residence_type" style="width:100%">
                <el-option label="城市" value="城市" />
                <el-option label="农村" value="农村" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="血糖水平">
              <el-input-number v-model="form.glucose_level" :precision="2" :step="1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="BMI">
              <el-input-number v-model="form.bmi" :precision="1" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
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
          <el-col :span="12">
            <el-form-item label="是否中风">
              <el-switch v-model="form.stroke" active-text="是" inactive-text="否" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPatients, addPatient, updatePatient, deletePatient } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const patients = ref([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const keyword = ref('')
const showDialog = ref(false)
const editMode = ref(false)
const saving = ref(false)

const form = reactive({
  id: null,
  name: '匿名',
  gender: '男性',
  age: 60,
  hypertension: 0,
  heart_disease: 0,
  married: 0,
  work_type: '私人企业',
  residence_type: '城市',
  glucose_level: 100,
  bmi: 25,
  smoking_status: '从不吸烟',
  stroke: 0
})

function resetForm() {
  Object.assign(form, {
    id: null, name: '匿名', gender: '男性', age: 60,
    hypertension: 0, heart_disease: 0, married: 0,
    work_type: '私人企业', residence_type: '城市',
    glucose_level: 100, bmi: 25, smoking_status: '从不吸烟', stroke: 0
  })
}

async function loadData() {
  try {
    const res = await getPatients({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    if (res.code === 200) {
      patients.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {}
}

function openEdit(row) {
  editMode.value = true
  Object.assign(form, row)
  showDialog.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editMode.value) {
      await updatePatient(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await addPatient(form)
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await deletePatient(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {}
}

function goPredict(row) {
  router.push({ path: '/prediction', query: { patient_id: row.id } })
}

onMounted(loadData)
</script>