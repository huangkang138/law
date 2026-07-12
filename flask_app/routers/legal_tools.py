"""
法律工具相关路由 - 完整版本
包含增删改查及批量操作
"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.db_models import (
    InterestCalculation,
    LaborCompensation,
    TrafficAccidentCompensation,
    CourtFee,
    WorkInjuryCompensation,
    LawyerFee,
    LegalCalendarEvent,
    LimitationCheck,
    ContractPenalty,
    PreservationFee,
    ExecutionFee,
    WillFee,
    AnnouncementFee,
    AppraisalFee,
    ArbitrationFee
)
import uuid
from datetime import datetime, timedelta
from services.labor_compensation_service import get_labor_compensation_service

router = Blueprint('legal_tools', __name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def serialize_record(record):
    """通用序列化方法"""
    data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
    if 'created_at' in data and data['created_at']:
        data['created_at'] = data['created_at'].isoformat()
    if 'updated_at' in data and data['updated_at']:
        data['updated_at'] = data['updated_at'].isoformat()
    if 'date' in data and data['date']:
        data['date'] = data['date'].isoformat()
    return data


# ==================== 利息计算 ====================

@router.route('/legal-tools/interest', methods=['POST'])
def calculate_interest():
    """计算利息"""
    try:
        data = request.get_json()
        principal = float(data.get('principal', 0))
        annual_rate = float(data.get('annual_rate', 0))
        days = int(data.get('days', 0))
        
        interest = principal * (annual_rate / 100) * (days / 365)
        total_amount = principal + interest
        
        db = next(get_db())
        record = InterestCalculation(
            id=str(uuid.uuid4()),
            principal=f"{principal:.2f}",
            annual_rate=f"{annual_rate:.2f}",
            days=days,
            interest=f"{interest:.2f}",
            total_amount=f"{total_amount:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                **serialize_record(record),
                'interest': round(interest, 2),
                'total_amount': round(total_amount, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/interest', methods=['GET'])
def get_interest_history():
    """获取利息计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(InterestCalculation)
        if search:
            query = query.filter(InterestCalculation.principal.contains(search))
        
        records = query.order_by(InterestCalculation.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/interest/<record_id>', methods=['DELETE'])
def delete_interest(record_id):
    """删除利息记录"""
    try:
        db = next(get_db())
        record = db.query(InterestCalculation).filter(InterestCalculation.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/interest/batch', methods=['DELETE'])
def batch_delete_interest():
    """批量删除利息记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(InterestCalculation).filter(InterestCalculation.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 劳动补偿 ====================

@router.route('/legal-tools/labor', methods=['POST'])
def calculate_labor_compensation():
    """计算劳动补偿金"""
    try:
        data = request.get_json()
        result = get_labor_compensation_service().calculate(
            data.get('monthly_salary', 0), data.get('years', 0), data.get('months', 0),
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/labor', methods=['GET'])
def get_labor_history():
    """获取劳动补偿计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(LaborCompensation)
        if search:
            query = query.filter(LaborCompensation.monthly_salary.contains(search))
        
        records = query.order_by(LaborCompensation.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/labor/<record_id>', methods=['DELETE'])
def delete_labor(record_id):
    """删除劳动补偿记录"""
    try:
        db = next(get_db())
        record = db.query(LaborCompensation).filter(LaborCompensation.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/labor/batch', methods=['DELETE'])
def batch_delete_labor():
    """批量删除劳动补偿记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(LaborCompensation).filter(LaborCompensation.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 交通事故赔偿 ====================

@router.route('/legal-tools/traffic', methods=['POST'])
def calculate_traffic_accident():
    """计算交通事故赔偿"""
    try:
        data = request.get_json()
        medical_expense = float(data.get('medical_expense', 0))
        lost_income = float(data.get('lost_income', 0))
        disability_level = int(data.get('disability_level', 10))
        
        disability_ratios = {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7, 5: 0.6, 
                             6: 0.5, 7: 0.4, 8: 0.3, 9: 0.2, 10: 0.1}
        disability_ratio = disability_ratios.get(disability_level, 0.1)
        
        base_compensation = 500000
        disability_compensation = base_compensation * disability_ratio
        nutrition_fee = 50 * 90
        care_fee = 150 * 90
        transportation_fee = 2000
        mental_damage = 50000 * disability_ratio
        
        total = medical_expense + lost_income + disability_compensation + \
                nutrition_fee + care_fee + transportation_fee + mental_damage
        
        details = {
            'medical_expense': medical_expense,
            'lost_income': lost_income,
            'disability_compensation': disability_compensation,
            'nutrition_fee': nutrition_fee,
            'care_fee': care_fee,
            'transportation_fee': transportation_fee,
            'mental_damage': mental_damage
        }
        
        db = next(get_db())
        record = TrafficAccidentCompensation(
            id=str(uuid.uuid4()),
            medical_expense=f"{medical_expense:.2f}",
            lost_income=f"{lost_income:.2f}",
            disability_level=disability_level,
            total_compensation=f"{total:.2f}",
            details=details
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'total_compensation': round(total, 2), 'details': details}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/traffic', methods=['GET'])
def get_traffic_history():
    """获取交通事故赔偿计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(TrafficAccidentCompensation)
        records = query.order_by(TrafficAccidentCompensation.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/traffic/<record_id>', methods=['DELETE'])
def delete_traffic(record_id):
    """删除交通事故赔偿记录"""
    try:
        db = next(get_db())
        record = db.query(TrafficAccidentCompensation).filter(TrafficAccidentCompensation.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/traffic/batch', methods=['DELETE'])
def batch_delete_traffic():
    """批量删除交通事故赔偿记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(TrafficAccidentCompensation).filter(TrafficAccidentCompensation.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 诉讼费用 ====================

@router.route('/legal-tools/court-fee', methods=['POST'])
def calculate_court_fee():
    """计算诉讼费用"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', 'property')
        amount = float(data.get('amount', 0))
        
        fee = 0
        if case_type == 'property':
            if amount <= 10000:
                fee = 50
            elif amount <= 100000:
                fee = 50 + (amount - 10000) * 0.025
            elif amount <= 200000:
                fee = 2300 + (amount - 100000) * 0.02
            elif amount <= 500000:
                fee = 4300 + (amount - 200000) * 0.015
            elif amount <= 1000000:
                fee = 8800 + (amount - 500000) * 0.01
            elif amount <= 2000000:
                fee = 13800 + (amount - 1000000) * 0.009
            elif amount <= 5000000:
                fee = 22800 + (amount - 2000000) * 0.008
            elif amount <= 10000000:
                fee = 46800 + (amount - 5000000) * 0.007
            elif amount <= 20000000:
                fee = 81800 + (amount - 10000000) * 0.006
            else:
                fee = 141800 + (amount - 20000000) * 0.005
        elif case_type == 'divorce':
            fee = 50 + (max(0, amount - 200000) * 0.005)
        elif case_type == 'labor':
            fee = 10
        elif case_type == 'other':
            fee = 50
        
        db = next(get_db())
        record = CourtFee(
            id=str(uuid.uuid4()),
            case_type=case_type,
            amount=f"{amount:.2f}",
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/court-fee', methods=['GET'])
def get_court_fee_history():
    """获取诉讼费计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(CourtFee)
        records = query.order_by(CourtFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/court-fee/<record_id>', methods=['DELETE'])
def delete_court_fee(record_id):
    """删除诉讼费记录"""
    try:
        db = next(get_db())
        record = db.query(CourtFee).filter(CourtFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/court-fee/batch', methods=['DELETE'])
def batch_delete_court_fee():
    """批量删除诉讼费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(CourtFee).filter(CourtFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 工伤赔偿 ====================

@router.route('/legal-tools/work-injury', methods=['POST'])
def calculate_work_injury():
    """计算工伤赔偿"""
    try:
        data = request.get_json()
        injury_level = int(data.get('injury_level', 10))
        monthly_salary = float(data.get('monthly_salary', 0))
        
        lump_sum_compensation = {1: 27, 2: 25, 3: 23, 4: 21, 5: 18, 
                                  6: 16, 7: 13, 8: 11, 9: 9, 10: 7}
        months = lump_sum_compensation.get(injury_level, 7)
        
        lump_sum = monthly_salary * months
        medical_treatment = 50000
        hospital_food = 30 * 90
        transportation = 2000
        care_fee = 150 * 90
        
        total = lump_sum + medical_treatment + hospital_food + transportation + care_fee
        
        details = {
            'lump_sum_compensation': lump_sum,
            'medical_treatment': medical_treatment,
            'hospital_food': hospital_food,
            'transportation': transportation,
            'care_fee': care_fee
        }
        
        db = next(get_db())
        record = WorkInjuryCompensation(
            id=str(uuid.uuid4()),
            injury_level=injury_level,
            monthly_salary=f"{monthly_salary:.2f}",
            total_compensation=f"{total:.2f}",
            details=details
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'total_compensation': round(total, 2), 'details': details}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/work-injury', methods=['GET'])
def get_work_injury_history():
    """获取工伤赔偿计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(WorkInjuryCompensation)
        records = query.order_by(WorkInjuryCompensation.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/work-injury/<record_id>', methods=['DELETE'])
def delete_work_injury(record_id):
    """删除工伤赔偿记录"""
    try:
        db = next(get_db())
        record = db.query(WorkInjuryCompensation).filter(WorkInjuryCompensation.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/work-injury/batch', methods=['DELETE'])
def batch_delete_work_injury():
    """批量删除工伤赔偿记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(WorkInjuryCompensation).filter(WorkInjuryCompensation.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 律师费 ====================

@router.route('/legal-tools/lawyer-fee', methods=['POST'])
def calculate_lawyer_fee():
    """计算律师费"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', 'civil')
        amount = float(data.get('amount', 0))
        fee_method = data.get('fee_method', 'percentage')
        
        fee = 0
        if fee_method == 'percentage':
            if case_type == 'civil':
                if amount <= 100000:
                    fee = amount * 0.08
                elif amount <= 500000:
                    fee = 8000 + (amount - 100000) * 0.06
                elif amount <= 1000000:
                    fee = 32000 + (amount - 500000) * 0.05
                elif amount <= 5000000:
                    fee = 57000 + (amount - 1000000) * 0.04
                else:
                    fee = 217000 + (amount - 5000000) * 0.03
            elif case_type == 'criminal':
                fee = 30000 + amount * 0.05
            elif case_type == 'administrative':
                fee = 20000 + amount * 0.04
        elif fee_method == 'fixed':
            if case_type == 'civil':
                fee = 10000
            elif case_type == 'criminal':
                fee = 50000
            elif case_type == 'administrative':
                fee = 30000
        
        db = next(get_db())
        record = LawyerFee(
            id=str(uuid.uuid4()),
            case_type=case_type,
            amount=f"{amount:.2f}",
            fee_method=fee_method,
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/lawyer-fee', methods=['GET'])
def get_lawyer_fee_history():
    """获取律师费计算历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(LawyerFee)
        records = query.order_by(LawyerFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/lawyer-fee/<record_id>', methods=['DELETE'])
def delete_lawyer_fee(record_id):
    """删除律师费记录"""
    try:
        db = next(get_db())
        record = db.query(LawyerFee).filter(LawyerFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/lawyer-fee/batch', methods=['DELETE'])
def batch_delete_lawyer_fee():
    """批量删除律师费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(LawyerFee).filter(LawyerFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 法律日历 ====================

@router.route('/legal-tools/calendar/events', methods=['POST'])
def create_calendar_event():
    """创建日历事件"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        event_type = data.get('event_type', 'custom')
        date_str = data.get('date', '')
        description = data.get('description', '')
        is_reminder = data.get('is_reminder', False)
        reminder_days = data.get('reminder_days', 7)
        
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        db = next(get_db())
        event = LegalCalendarEvent(
            id=str(uuid.uuid4()),
            title=title,
            event_type=event_type,
            date=date,
            description=description,
            is_reminder=is_reminder,
            reminder_days=reminder_days
        )
        db.add(event)
        db.commit()
        
        return jsonify({'success': True, 'data': serialize_record(event)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/calendar/events', methods=['GET'])
def get_calendar_events():
    """获取日历事件"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        event_type = request.args.get('event_type', '')
        
        query = db.query(LegalCalendarEvent)
        if search:
            query = query.filter(LegalCalendarEvent.title.contains(search))
        if event_type:
            query = query.filter(LegalCalendarEvent.event_type == event_type)
        
        events = query.order_by(LegalCalendarEvent.date).all()
        return jsonify({'success': True, 'data': [serialize_record(e) for e in events]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/calendar/events/<event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    """更新日历事件"""
    try:
        data = request.get_json()
        db = next(get_db())
        event = db.query(LegalCalendarEvent).filter(LegalCalendarEvent.id == event_id).first()
        if not event:
            return jsonify({'success': False, 'message': '事件不存在'}), 404
        
        if 'title' in data:
            event.title = data['title']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'date' in data:
            event.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
        if 'description' in data:
            event.description = data['description']
        if 'is_reminder' in data:
            event.is_reminder = data['is_reminder']
        if 'reminder_days' in data:
            event.reminder_days = data['reminder_days']
        if 'is_completed' in data:
            event.is_completed = data['is_completed']
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/calendar/events/<event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    """删除日历事件"""
    try:
        db = next(get_db())
        event = db.query(LegalCalendarEvent).filter(LegalCalendarEvent.id == event_id).first()
        if not event:
            return jsonify({'success': False, 'message': '事件不存在'}), 404
        
        db.delete(event)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/calendar/events/batch', methods=['DELETE'])
def batch_delete_calendar_events():
    """批量删除日历事件"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(LegalCalendarEvent).filter(LegalCalendarEvent.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/calendar/events/batch-complete', methods=['PUT'])
def batch_complete_calendar_events():
    """批量标记完成日历事件"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        is_completed = data.get('is_completed', True)
        db = next(get_db())
        db.query(LegalCalendarEvent).filter(LegalCalendarEvent.id.in_(ids)).update(
            {'is_completed': is_completed},
            synchronize_session=False
        )
        db.commit()
        return jsonify({'success': True, 'updated_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 诉讼时效 ====================

@router.route('/legal-tools/limitation', methods=['POST'])
def check_limitation():
    """检查诉讼时效"""
    try:
        data = request.get_json()
        case_type = data.get('case_type', 'general')
        incident_date_str = data.get('incident_date', '')
        
        limitation_periods = {
            'general': 3,
            'personal_injury': 1,
            'product_quality': 2,
            'environmental': 3,
            'contract': 3,
            'property': 3
        }
        
        period = limitation_periods.get(case_type, 3)
        incident_date = datetime.fromisoformat(incident_date_str.replace('Z', '+00:00'))
        expiration_date = incident_date + timedelta(days=period * 365)
        is_expired = datetime.now() > expiration_date
        
        db = next(get_db())
        record = LimitationCheck(
            id=str(uuid.uuid4()),
            case_type=case_type,
            incident_date=incident_date_str,
            limitation_period=period,
            expiration_date=expiration_date.isoformat(),
            is_expired=is_expired
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'limitation_period': period, 'expiration_date': expiration_date.isoformat(), 'is_expired': is_expired}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/limitation', methods=['GET'])
def get_limitation_history():
    """获取诉讼时效查询历史"""
    try:
        db = next(get_db())
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        query = db.query(LimitationCheck)
        records = query.order_by(LimitationCheck.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/limitation/<record_id>', methods=['DELETE'])
def delete_limitation(record_id):
    """删除诉讼时效记录"""
    try:
        db = next(get_db())
        record = db.query(LimitationCheck).filter(LimitationCheck.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/limitation/batch', methods=['DELETE'])
def batch_delete_limitation():
    """批量删除诉讼时效记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(LimitationCheck).filter(LimitationCheck.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 合同违约金 ====================

@router.route('/legal-tools/contract-penalty', methods=['POST'])
def calculate_contract_penalty():
    """计算合同违约金"""
    try:
        data = request.get_json()
        contract_amount = float(data.get('contract_amount', 0))
        penalty_rate = float(data.get('penalty_rate', 0))
        delay_days = int(data.get('delay_days', 0))
        
        penalty_amount = contract_amount * (penalty_rate / 100) * delay_days
        total_amount = contract_amount + penalty_amount
        
        db = next(get_db())
        record = ContractPenalty(
            id=str(uuid.uuid4()),
            contract_amount=f"{contract_amount:.2f}",
            penalty_rate=f"{penalty_rate:.2f}",
            delay_days=delay_days,
            penalty_amount=f"{penalty_amount:.2f}",
            total_amount=f"{total_amount:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'penalty_amount': round(penalty_amount, 2), 'total_amount': round(total_amount, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/contract-penalty', methods=['GET'])
def get_contract_penalty_history():
    """获取合同违约金计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(ContractPenalty).order_by(ContractPenalty.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/contract-penalty/<record_id>', methods=['DELETE'])
def delete_contract_penalty(record_id):
    """删除合同违约金记录"""
    try:
        db = next(get_db())
        record = db.query(ContractPenalty).filter(ContractPenalty.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/contract-penalty/batch', methods=['DELETE'])
def batch_delete_contract_penalty():
    """批量删除合同违约金记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(ContractPenalty).filter(ContractPenalty.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 保全费 ====================

@router.route('/legal-tools/preservation-fee', methods=['POST'])
def calculate_preservation_fee():
    """计算保全费"""
    try:
        data = request.get_json()
        preservation_amount = float(data.get('preservation_amount', 0))
        
        fee = 0
        if preservation_amount <= 1000:
            fee = 30
        elif preservation_amount <= 100000:
            fee = 30 + (preservation_amount - 1000) * 0.01
        else:
            fee = 1020 + (preservation_amount - 100000) * 0.005
            fee = min(fee, 5000)
        
        db = next(get_db())
        record = PreservationFee(
            id=str(uuid.uuid4()),
            preservation_amount=f"{preservation_amount:.2f}",
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/preservation-fee', methods=['GET'])
def get_preservation_fee_history():
    """获取保全费计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(PreservationFee).order_by(PreservationFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/preservation-fee/<record_id>', methods=['DELETE'])
def delete_preservation_fee(record_id):
    """删除保全费记录"""
    try:
        db = next(get_db())
        record = db.query(PreservationFee).filter(PreservationFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/preservation-fee/batch', methods=['DELETE'])
def batch_delete_preservation_fee():
    """批量删除保全费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(PreservationFee).filter(PreservationFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 执行费 ====================

@router.route('/legal-tools/execution-fee', methods=['POST'])
def calculate_execution_fee():
    """计算执行费"""
    try:
        data = request.get_json()
        execution_amount = float(data.get('execution_amount', 0))
        
        fee = 0
        if execution_amount <= 10000:
            fee = 50
        elif execution_amount <= 500000:
            fee = 50 + (execution_amount - 10000) * 0.015
        elif execution_amount <= 5000000:
            fee = 7400 + (execution_amount - 500000) * 0.01
        elif execution_amount <= 10000000:
            fee = 52400 + (execution_amount - 5000000) * 0.005
        else:
            fee = 77400 + (execution_amount - 10000000) * 0.001
        
        db = next(get_db())
        record = ExecutionFee(
            id=str(uuid.uuid4()),
            execution_amount=f"{execution_amount:.2f}",
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/execution-fee', methods=['GET'])
def get_execution_fee_history():
    """获取执行费计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(ExecutionFee).order_by(ExecutionFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/execution-fee/<record_id>', methods=['DELETE'])
def delete_execution_fee(record_id):
    """删除执行费记录"""
    try:
        db = next(get_db())
        record = db.query(ExecutionFee).filter(ExecutionFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/execution-fee/batch', methods=['DELETE'])
def batch_delete_execution_fee():
    """批量删除执行费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(ExecutionFee).filter(ExecutionFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 遗嘱费用 ====================

@router.route('/legal-tools/will-fee', methods=['POST'])
def calculate_will_fee():
    """计算遗嘱费用"""
    try:
        data = request.get_json()
        estate_value = float(data.get('estate_value', 0))
        will_type = data.get('will_type', 'notary')
        
        notary_fee = 0
        if will_type == 'notary':
            if estate_value <= 200000:
                notary_fee = 200
            elif estate_value <= 500000:
                notary_fee = 200 + (estate_value - 200000) * 0.002
            elif estate_value <= 1000000:
                notary_fee = 800 + (estate_value - 500000) * 0.0015
            else:
                notary_fee = 1550 + (estate_value - 1000000) * 0.001
        elif will_type == 'self_written':
            notary_fee = 0
        
        attorney_fee = max(5000, estate_value * 0.01)
        total_fee = notary_fee + attorney_fee
        
        db = next(get_db())
        record = WillFee(
            id=str(uuid.uuid4()),
            estate_value=f"{estate_value:.2f}",
            will_type=will_type,
            notary_fee=f"{notary_fee:.2f}",
            attorney_fee=f"{attorney_fee:.2f}",
            total_fee=f"{total_fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                **serialize_record(record),
                'notary_fee': round(notary_fee, 2),
                'attorney_fee': round(attorney_fee, 2),
                'total_fee': round(total_fee, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/will-fee', methods=['GET'])
def get_will_fee_history():
    """获取遗嘱费用计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(WillFee).order_by(WillFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/will-fee/<record_id>', methods=['DELETE'])
def delete_will_fee(record_id):
    """删除遗嘱费用记录"""
    try:
        db = next(get_db())
        record = db.query(WillFee).filter(WillFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/will-fee/batch', methods=['DELETE'])
def batch_delete_will_fee():
    """批量删除遗嘱费用记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(WillFee).filter(WillFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 公告费 ====================

@router.route('/legal-tools/announcement-fee', methods=['POST'])
def calculate_announcement_fee():
    """计算公告费"""
    try:
        data = request.get_json()
        announcement_type = data.get('announcement_type', 'court')
        media_type = data.get('media_type', 'newspaper')
        times = int(data.get('times', 1))
        
        base_fees = {
            'court': {'newspaper': 300, 'online': 200, 'both': 400},
            'arbitration': {'newspaper': 400, 'online': 300, 'both': 500},
            'notary': {'newspaper': 200, 'online': 150, 'both': 300}
        }
        
        base_fee = base_fees.get(announcement_type, {}).get(media_type, 300)
        fee = base_fee * times
        
        db = next(get_db())
        record = AnnouncementFee(
            id=str(uuid.uuid4()),
            announcement_type=announcement_type,
            media_type=media_type,
            times=times,
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/announcement-fee', methods=['GET'])
def get_announcement_fee_history():
    """获取公告费计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(AnnouncementFee).order_by(AnnouncementFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/announcement-fee/<record_id>', methods=['DELETE'])
def delete_announcement_fee(record_id):
    """删除公告费记录"""
    try:
        db = next(get_db())
        record = db.query(AnnouncementFee).filter(AnnouncementFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/announcement-fee/batch', methods=['DELETE'])
def batch_delete_announcement_fee():
    """批量删除公告费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(AnnouncementFee).filter(AnnouncementFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 鉴定费 ====================

@router.route('/legal-tools/appraisal-fee', methods=['POST'])
def calculate_appraisal_fee():
    """计算鉴定费"""
    try:
        data = request.get_json()
        appraisal_type = data.get('appraisal_type', 'forensic')
        subject_value = float(data.get('subject_value', 0))
        
        fee_rates = {
            'forensic': 0.01,
            'medical': 0.008,
            'property': 0.006,
            'document': 0.005
        }
        
        base_fee = 2000
        rate = fee_rates.get(appraisal_type, 0.008)
        fee = base_fee + subject_value * rate
        fee = max(fee, base_fee)
        
        db = next(get_db())
        record = AppraisalFee(
            id=str(uuid.uuid4()),
            appraisal_type=appraisal_type,
            subject_value=f"{subject_value:.2f}",
            fee=f"{fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {**serialize_record(record), 'fee': round(fee, 2)}
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/appraisal-fee', methods=['GET'])
def get_appraisal_fee_history():
    """获取鉴定费计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(AppraisalFee).order_by(AppraisalFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/appraisal-fee/<record_id>', methods=['DELETE'])
def delete_appraisal_fee(record_id):
    """删除鉴定费记录"""
    try:
        db = next(get_db())
        record = db.query(AppraisalFee).filter(AppraisalFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/appraisal-fee/batch', methods=['DELETE'])
def batch_delete_appraisal_fee():
    """批量删除鉴定费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(AppraisalFee).filter(AppraisalFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== 仲裁费 ====================

@router.route('/legal-tools/arbitration-fee', methods=['POST'])
def calculate_arbitration_fee():
    """计算仲裁费"""
    try:
        data = request.get_json()
        arbitration_amount = float(data.get('arbitration_amount', 0))
        
        case_handling_fee = 0
        arbitration_fee = 0
        
        if arbitration_amount <= 100000:
            case_handling_fee = 400
            arbitration_fee = arbitration_amount * 0.05
        elif arbitration_amount <= 500000:
            case_handling_fee = 400 + (arbitration_amount - 100000) * 0.004
            arbitration_fee = 5000 + (arbitration_amount - 100000) * 0.04
        elif arbitration_amount <= 1000000:
            case_handling_fee = 2000 + (arbitration_amount - 500000) * 0.003
            arbitration_fee = 21000 + (arbitration_amount - 500000) * 0.03
        elif arbitration_amount <= 5000000:
            case_handling_fee = 3500 + (arbitration_amount - 1000000) * 0.002
            arbitration_fee = 36000 + (arbitration_amount - 1000000) * 0.02
        else:
            case_handling_fee = 11500 + (arbitration_amount - 5000000) * 0.001
            arbitration_fee = 116000 + (arbitration_amount - 5000000) * 0.01
        
        total_fee = case_handling_fee + arbitration_fee
        
        db = next(get_db())
        record = ArbitrationFee(
            id=str(uuid.uuid4()),
            arbitration_amount=f"{arbitration_amount:.2f}",
            case_handling_fee=f"{case_handling_fee:.2f}",
            arbitration_fee=f"{arbitration_fee:.2f}",
            total_fee=f"{total_fee:.2f}"
        )
        db.add(record)
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                **serialize_record(record),
                'case_handling_fee': round(case_handling_fee, 2),
                'arbitration_fee': round(arbitration_fee, 2),
                'total_fee': round(total_fee, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/arbitration-fee', methods=['GET'])
def get_arbitration_fee_history():
    """获取仲裁费计算历史"""
    try:
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        records = db.query(ArbitrationFee).order_by(ArbitrationFee.created_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'data': [serialize_record(r) for r in records]})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/arbitration-fee/<record_id>', methods=['DELETE'])
def delete_arbitration_fee(record_id):
    """删除仲裁费记录"""
    try:
        db = next(get_db())
        record = db.query(ArbitrationFee).filter(ArbitrationFee.id == record_id).first()
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        db.delete(record)
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/arbitration-fee/batch', methods=['DELETE'])
def batch_delete_arbitration_fee():
    """批量删除仲裁费记录"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        db = next(get_db())
        db.query(ArbitrationFee).filter(ArbitrationFee.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


# ==================== UML 图表生成 ====================

@router.route('/legal-tools/uml-diagram', methods=['POST'])
def generate_uml_diagram():
    """生成 UML 图表"""
    try:
        import os
        import subprocess
        import tempfile
        from models.db_models import UMLDiagram
        
        data = request.get_json()
        diagram_type = data.get('diagram_type', 'plantuml')
        diagram_source = data.get('diagram_source', '')
        output_format = data.get('output_format', 'svg')
        
        # 验证参数
        if not diagram_source:
            return jsonify({'success': False, 'message': '图表源代码不能为空'}), 400
        
        if diagram_type not in ['plantuml', 'mermaid', 'graphviz']:
            return jsonify({'success': False, 'message': '不支持的图表类型'}), 400
        
        if output_format not in ['svg', 'png', 'pdf', 'jpeg']:
            return jsonify({'success': False, 'message': '不支持的输出格式'}), 400
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{diagram_type}' if diagram_type != 'graphviz' else '.dot', delete=False) as f:
            f.write(diagram_source)
            temp_file_path = f.name
        
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'uml')
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件路径
        import uuid
        output_filename = f"{uuid.uuid4()}.{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # 调用 Kroki.io API
        kroki_url = f"https://kroki.io/{diagram_type}/{output_format}"
        
        # 使用 curl 命令发送 POST 请求
        curl_cmd = [
            'curl', '-s', '-X', 'POST', kroki_url,
            '-H', 'Content-Type: text/plain',
            '--data-binary', f'@{temp_file_path}',
            '-o', output_path
        ]
        
        # 执行 curl 命令
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        # 清理临时文件
        os.unlink(temp_file_path)
        
        # 检查命令执行结果
        if result.returncode != 0:
            return jsonify({'success': False, 'message': f'生成图表失败: {result.stderr}'}), 400
        
        # 检查输出文件是否生成
        if not os.path.exists(output_path):
            return jsonify({'success': False, 'message': '生成图表失败，未找到输出文件'}), 400
        
        # 保存到数据库
        db = next(get_db())
        record = UMLDiagram(
            id=str(uuid.uuid4()),
            diagram_type=diagram_type,
            diagram_source=diagram_source,
            output_format=output_format,
            output_path=output_path
        )
        db.add(record)
        db.commit()
        
        # 生成可访问的 URL
        relative_path = os.path.relpath(output_path, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        access_url = f"/uploads/uml/{output_filename}"
        
        return jsonify({
            'success': True,
            'data': {
                'id': record.id,
                'diagram_type': diagram_type,
                'output_format': output_format,
                'output_path': output_path,
                'access_url': access_url,
                'created_at': record.created_at.isoformat() if record.created_at else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/uml-diagram', methods=['GET'])
def get_uml_diagram_history():
    """获取 UML 图表生成历史"""
    try:
        from models.db_models import UMLDiagram
        
        db = next(get_db())
        limit = int(request.args.get('limit', 100))
        
        records = db.query(UMLDiagram).order_by(UMLDiagram.created_at.desc()).limit(limit).all()
        
        # 生成可访问的 URL
        result = []
        for record in records:
            output_filename = os.path.basename(record.output_path)
            access_url = f"/uploads/uml/{output_filename}"
            result.append({
                'id': record.id,
                'diagram_type': record.diagram_type,
                'output_format': record.output_format,
                'access_url': access_url,
                'created_at': record.created_at.isoformat() if record.created_at else None
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/uml-diagram/<record_id>', methods=['DELETE'])
def delete_uml_diagram(record_id):
    """删除 UML 图表记录"""
    try:
        import os
        from models.db_models import UMLDiagram
        
        db = next(get_db())
        record = db.query(UMLDiagram).filter(UMLDiagram.id == record_id).first()
        
        if not record:
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        # 删除文件
        if os.path.exists(record.output_path):
            try:
                os.unlink(record.output_path)
            except:
                pass
        
        # 删除数据库记录
        db.delete(record)
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@router.route('/legal-tools/uml-diagram/batch', methods=['DELETE'])
def batch_delete_uml_diagram():
    """批量删除 UML 图表记录"""
    try:
        import os
        from models.db_models import UMLDiagram
        
        data = request.get_json()
        ids = data.get('ids', [])
        
        db = next(get_db())
        records = db.query(UMLDiagram).filter(UMLDiagram.id.in_(ids)).all()
        
        # 删除文件
        for record in records:
            if os.path.exists(record.output_path):
                try:
                    os.unlink(record.output_path)
                except:
                    pass
        
        # 删除数据库记录
        db.query(UMLDiagram).filter(UMLDiagram.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        
        return jsonify({'success': True, 'deleted_count': len(ids)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
