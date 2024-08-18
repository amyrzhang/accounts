import Vue from 'vue';
import VueRouter from 'vue-router';
import IncomeExpenditure from '../views/IncomeExpenditure.vue';
import AssetManagement from '../views/AssetManagement.vue';
import StatisticsAnalysis from '../views/StatisticsAnalysis.vue';

Vue.use(VueRouter);

const routes = [
  { path: '/', redirect: '/income-expenditure' },
  { path: '/income-expenditure', component: IncomeExpenditure },
  { path: '/asset-management', component: AssetManagement },
  { path: '/statistics-analysis', component: StatisticsAnalysis },
];

const router = new VueRouter({
  routes,
});

export default router;
