<template>
  <div>
    <button @click="filterData">Filter</button>
    <table>
      <thead>
        <tr>
          <th>Transaction Time</th>
          <th>Source</th>
          <th>Income/Expenditure</th>
          <th>Payment Status</th>
          <th>Type</th>
          <th>Category</th>
          <th>Counterparty</th>
          <th>Product</th>
          <th>Write-off</th>
          <th>Amount</th>
          <th>Payment Method</th>
          <th>Processed Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in data" :key="index">
          <td>{{ item.transactionTime }}</td>
          <td>{{ item.source }}</td>
          <td>{{ item.incomeExpenditure }}</td>
          <td>{{ item.paymentStatus }}</td>
          <td>{{ item.type }}</td>
          <td>{{ item.category }}</td>
          <td>{{ item.counterparty }}</td>
          <td>{{ item.product }}</td>
          <td>{{ item.writeOff }}</td>
          <td>{{ item.amount }}</td>
          <td>{{ item.paymentMethod }}</td>
          <td>{{ item.processedAmount }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: ['data'],
  methods: {
    filterData() {
      // Add filter logic here
    },
  },
};
</script>
