<template>
  <div>
    <h1>Income and Expenditure Management</h1>
    <input type="file" @change="importData" />
    <IncomeExpenditureTable :data="tableData" />
  </div>
</template>

<script>
import IncomeExpenditureTable from '@/components/IncomeExpenditureTable.vue';

export default {
  components: {
    IncomeExpenditureTable,
  },
  data() {
    return {
      tableData: [],
    };
  },
  methods: {
    importData(event) {
      const file = event.target.files[0];
      // Add logic to handle file import and update tableData
    },
  },
};
</script>
